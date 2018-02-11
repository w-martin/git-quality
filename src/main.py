""" Main entry point """
import logging
import os
import shutil
import tempfile
from contextlib import contextmanager

import click
import datetime
import numpy as np
import pandas as pd
import sklearn.preprocessing

import gitparser
import graphs
import reporting

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
    os.system('git log --use-mailmap --no-merges --stat > {log_filename}'.format(log_filename=log_filename))
    with open(log_filename, 'r') as f:
        result = f.read()
    shutil.rmtree(tempdir, ignore_errors=True)
    logging.info('Fetched commit log')
    return result


def convert_prs_to_dateframe(commits, date_start, date_end):
    """ Converts a list of PullRequests to a pandas dataframe indexed by date
    :param list[gitparser.PullRequest] commits: the list of commits to convert
    :return: a pandas dataframe with a row per commit
    :rtype: pd.DataFrame
    """
    df = pd.DataFrame(commits, columns=gitparser.PR_COLUMNS)
    df = format_commit_df(df, date_start, date_end)
    # one hot columns for reviewers
    mlb = sklearn.preprocessing.MultiLabelBinarizer()
    df = df.join(pd.DataFrame(mlb.fit_transform(df.pop(gitparser.REVIEWERS)),
                              columns=mlb.classes_, index=df.index))
    return df


def convert_commits_to_dateframe(commits, date_start, date_end):
    """ Converts a list of Commits to a pandas dataframe indexed by date
    :param list[gitparser.Commit] commits: the list of commits to convert
    :return: a pandas dataframe with a row per commit
    :rtype: pd.DataFrame
    """
    df = pd.DataFrame(commits, columns=gitparser.COMMIT_COLUMNS)
    df = format_commit_df(df, date_start, date_end)
    return df


def format_commit_df(df, date_start, date_end):
    # handle date
    df[gitparser.DATE] = pd.to_datetime(df[gitparser.DATE], errors='coerce')
    df.set_index([gitparser.DATE], inplace=True)
    df['month'] = df.index.strftime("%b'%y")
    df['week'] = df.index.strftime("%b'%U'%y")
    new_df = df[(df.index >= date_start) & (df.index < date_end)].sort_index()
    logging.info('Reduced commits from {initial_count:d} to {end_count:d} on date'.format(
        initial_count=df.shape[0], end_count=new_df.shape[0]))
    return new_df


def compute_awards(merge_df):
    # reviewed more than usual - well done
    # more changes than usual (code only) - well done
    # net deleter of the month
    # consider smaller PRs (PR changes above avg in month)
    return pd.DataFrame()


def compute_daterange():
    today = datetime.date.today()
    year = today.year - 1
    month = today.month - 1
    if 0 == month:
        month = 12
        year -= 1
    start = datetime.datetime(year, month, 1)
    end = datetime.datetime(today.year, today.month, 1)
    return start, end


@click.command()
@click.option('--directory', required=True, help='Assess quality of the repo at the given path')
@click.option('--output', required=True, help='Save graphs and stats to the given directory')
@click.option('--srcpath')
@click.option('--resume', is_flag=True, help='Load previously saved dataframe, if present')
@click.option('--email', default=None, type=str, help='Email last month\'s summary to this address if set')
@click.option('--authors/--no-authors', default=True)
def main(directory, output, srcpath='/opt/git-quality', resume=False, email=None, authors=True):
    results_path = os.path.join(output, 'prs.csv')
    date_start, date_end = compute_daterange()
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
        pr_df = convert_prs_to_dateframe(merges, date_start, date_end)

        # ensure output directory exists
        output = os.path.abspath(output)
        try:
            os.makedirs(output)
        except OSError:
            pass
        try:
            pr_df.to_csv(results_path)
        except OSError:
            pass

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
        commit_df = convert_commits_to_dateframe(commits, date_start, date_end)

        # ensure output directory exists
        output = os.path.abspath(output)
        try:
            os.makedirs(output)
        except OSError:
            pass
        try:
            commit_df.to_csv(results_path)
        except OSError:
            pass

    # filter for author
    date_threshold = pr_df.index.max().to_pydatetime() - datetime.timedelta(days=365 / 3)
    recent_authors = np.sort(pr_df[pr_df.index > date_threshold][gitparser.AUTHOR].unique())
    # plot graphs
    graphs.plot_pr_stats(pr_df, output, authors=recent_authors, review_authors=recent_authors)
    graphs.plot_commit_stats(commit_df, output, authors=recent_authors)
    repo_name = os.path.basename(directory)
    # copy web template to view them
    nav = '<ul>{items}</ul>'.format(items=''.join(
        ['<li><a href="{name}/">{name}</a></li>'.format(name=a.replace(' ', '_')) for a in recent_authors]))
    target_path = os.path.join(output, 'index.html')
    with open(os.path.join(srcpath, 'templates', 'index.html'), 'r') as f:
        page_text = f.read()
    with open(target_path, 'w') as f:
        f.write(page_text.format(name=repo_name, nav=nav))

    if authors:
        for author_name in recent_authors:
            # plot graphs
            directory = os.path.join(output, author_name.replace(' ', '_'))
            os.makedirs(directory, exist_ok=True)
            graphs.plot_pr_stats(pr_df, directory, authors=[author_name], review_authors=recent_authors)
            graphs.plot_commit_stats(commit_df, directory, authors=[author_name])
            # copy web template to view them
            target_path = os.path.join(directory, 'index.html')
            with open(target_path, 'w') as f:
                f.write(page_text.format(name=author_name, nav=''))

    # email award winners
    if email:
        metrics_df = compute_awards(pr_df)
        reporting.email_awards(email, metrics_df[:1], repo_name, srcpath=srcpath)


if __name__ == '__main__':
    main()
