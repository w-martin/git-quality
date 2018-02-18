""" Main entry point """
import datetime
import htmls
import logging
import os
import shutil
import tempfile
from contextlib import contextmanager
import itertools

import click
import numpy as np
import pandas as pd
import sklearn.preprocessing

import gitparser
import graphs
import reporting
import util

logging.basicConfig(level=logging.INFO)

# temporarily save the git log to this file and delete it afterwards
GITMERGE_FILENAME = 'git_merges.log'
GITCOMMIT_FILENAME = 'git_commits.log'


@contextmanager
def cd(directory):
    current_dir = os.getcwd()
    os.chdir(directory)
    yield
    os.chdir(current_dir)


def load_pr_log():
    """ Loads the pr commit log from the given directory
    :return: the commit log
    :rtype: str
    """
    tempdir = tempfile.gettempdir()
    log_filename = os.path.join(tempdir, GITMERGE_FILENAME)
    os.system('git log --use-mailmap --merges > {log_filename}'.format(log_filename=log_filename))
    with open(log_filename, 'r') as f:
        result = f.read()
    shutil.rmtree(tempdir, ignore_errors=True)
    logging.info('Fetched pr log')
    return result


def load_commit_log():
    """ Loads the commit log from the given directory
    :return: the commit log
    :rtype: str
    """
    tempdir = tempfile.gettempdir()
    log_filename = os.path.join(tempdir, GITCOMMIT_FILENAME)
    os.system('git log --use-mailmap --no-merges --all --stat > {log_filename}'.format(log_filename=log_filename))
    with open(log_filename, 'r') as f:
        result = f.read()
    shutil.rmtree(tempdir, ignore_errors=True)
    logging.info('Fetched commit log')
    return result


def convert_prs_to_dateframe(commits):
    """ Converts a list of PullRequests to a pandas dataframe indexed by date
    :param list[gitparser.PullRequest] commits: the list of commits to convert
    :return: a pandas dataframe with a row per commit
    :rtype: pd.DataFrame
    """
    df = pd.DataFrame(commits, columns=gitparser.PR_COLUMNS)
    format_commit_df(df)
    # one hot columns for reviewers
    mlb = sklearn.preprocessing.MultiLabelBinarizer()
    df = df.join(pd.DataFrame(mlb.fit_transform(df.pop(gitparser.REVIEWERS)),
                              columns=mlb.classes_, index=df.index))
    return df


def convert_commits_to_dateframe(commits):
    """ Converts a list of Commits to a pandas dataframe indexed by date
    :param list[gitparser.Commit] commits: the list of commits to convert
    :return: a pandas dataframe with a row per commit
    :rtype: pd.DataFrame
    """
    df = pd.DataFrame(commits, columns=gitparser.COMMIT_COLUMNS)
    format_commit_df(df)
    return df


def format_commit_df(df):
    # handle date
    df[gitparser.DATE] = pd.to_datetime(df[gitparser.DATE], errors='coerce')
    df.set_index([gitparser.DATE], inplace=True)
    df['month'] = df['M'] = df.index.strftime("%b'%y")
    df['week'] = df['W'] = df.index.strftime("%b'%U'%y")


def compute_dateranges():
    today = datetime.datetime.today()
    month_12 = (today - datetime.timedelta(days=365), '', '12 months')
    month_6 = (today - datetime.timedelta(days=183), '6_months/', '6 months')
    month_3 = (today - datetime.timedelta(days=92), '3_months/', '3 months')
    month_1 = (today - datetime.timedelta(days=28), '1_month/', '1 month')
    weeks_1 = (today - datetime.timedelta(days=7), '7_days/', '7 days')
    return month_12, month_6, month_3, month_1, weeks_1


@click.command()
@click.option('--directory', required=True, help='Assess quality of the repo at the given path')
@click.option('--output', required=True, help='Save graphs and stats to the given directory')
@click.option('--srcpath')
@click.option('--resume', is_flag=True, help='Load previously saved dataframe, if present')
@click.option('--email/--no-email', default=True, help='Email last month\'s summary to this address if set')
@click.option('--plotgraphs/--no-plotgraphs', default=True)
def main(directory, output, srcpath='/opt/git-quality', resume=False, email=True, plotgraphs=True):
    pr_df = fetch_pr_df(directory, output, resume).sort_index()
    commit_df = fetch_commit_df(directory, output, resume).sort_index()

    # copy web template to view them
    home_url = util.read_config('server')['url']
    repo_name = os.path.basename(directory)

    # filter for author
    recent_authors = compute_recent_authors(pr_df)

    if email:
        reporting.run_tracking(pr_df, commit_df, srcpath, output, repo_name, home_url, recent_authors)

    with open(os.path.join(srcpath, 'templates', 'index.html'), 'r') as f:
        page_text = f.read()

    for (date_from, timeframe, timeframe_text), (view, frequency, view_text), author in \
            itertools.product(compute_dateranges(),
                              [('', 'M', 'Monthly'), ('weekly/', 'W', 'Weekly'), ('daily/', 'D', 'Daily')],
                              [''] + recent_authors):

        target_path = os.path.join(output, view, timeframe, author.replace(' ', '_'), 'index.html')
        print(target_path)
        dirname = os.path.dirname(target_path)
        os.makedirs(dirname, exist_ok=True)
        shutil.copy(os.path.join(srcpath, 'templates', 'styles.css'), os.path.join(dirname, 'styles.css'))
        with open(target_path, 'w') as f:
            f.write(page_text.format(name=repo_name if '' == author else author,
                                     nav=htmls.compute_nav(home_url, view, timeframe, recent_authors),
                                     home_url=home_url, timeframe=timeframe, view=view,
                                     author='' if '' == author else author.replace(' ', '_') + '/',
                                     timeframe_text=timeframe_text, view_text=view_text))
        # plot graphs
        if plotgraphs:
            graphs.plot_pr_stats(pr_df, dirname,
                                 authors=recent_authors if '' == author else [author], start_date=date_from,
                                 frequency=frequency, view_text=view_text, review_authors=recent_authors)
            graphs.plot_commit_stats(commit_df, dirname, start_date=date_from,
                                     frequency=frequency, view_text=view_text,
                                     authors=recent_authors if '' == author else [author])


def compute_recent_authors(pr_df):
    date_threshold = pr_df.index.max().to_pydatetime() - datetime.timedelta(days=365 / 3)
    recent_authors = np.sort(pr_df[pr_df.index > date_threshold][gitparser.AUTHOR].unique())
    recent_authors = [ra.strip().replace('\n', '') for ra in recent_authors]
    return recent_authors


def fetch_commit_df(directory, output, resume):
    results_path = os.path.join(output, 'commits.csv')
    commit_df = None
    if resume:
        try:
            commit_df = pd.read_csv(results_path, parse_dates=True, index_col=0)
        except OSError:
            pass
    if commit_df is None:
        # load the git log and parse it
        commits = []
        for d in directory.split(','):
            with cd(d):
                log_text = load_commit_log()
                commits += gitparser.extract_commits(log_text)
        commit_df = convert_commits_to_dateframe(commits)

        # ensure output directory exists
        os.makedirs(output, exist_ok=True)
        try:
            commit_df.to_csv(results_path)
        except OSError:
            pass
    return commit_df


def fetch_pr_df(directory, output, resume):
    results_path = os.path.join(output, 'prs.csv')
    pr_df = None
    if resume:
        try:
            pr_df = pd.read_csv(results_path, parse_dates=True, index_col=0)
        except OSError:
            pass
    if pr_df is None:
        # load the git log and parse it
        merges = []
        for d in directory.split(','):
            with cd(d):
                log_text = load_pr_log()
                pr_commits = gitparser.extract_pull_requests(log_text)
                merges += pr_commits

        logging.info("Extracted {no_merges:d} merged pull requests".format(no_merges=len(merges)))

        # convert to pandas dataframe
        pr_df = convert_prs_to_dateframe(merges)

        # ensure output directory exists
        os.makedirs(output, exist_ok=True)
        try:
            pr_df.to_csv(results_path)
        except OSError:
            pass
    return pr_df


if __name__ == '__main__':
    main()
