""" Main entry point """
import datetime
import logging
import os
import shutil
import tempfile
from contextlib import contextmanager

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
    format_commit_df(df)
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
    format_commit_df(df)
    return df


def format_commit_df(df):
    # handle date
    df[gitparser.DATE] = pd.to_datetime(df[gitparser.DATE], errors='coerce')
    df.set_index([gitparser.DATE], inplace=True)
    df['month'] = df['M'] = df.index.strftime("%b'%y")
    df['week'] = df['W'] = df.index.strftime("%b'%U'%y")


def reduce_df(df, date_start, date_end):
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


def run_tracking(pr_df, commit_df, srcpath, output, repo_name, home_url, recent_authors):
    config = util.read_config('summary')
    email = config['email']
    day = config['day']
    today = datetime.datetime.today()
    is_today = today.strftime('%A') == day
    objectives = config['objectives']
    authors = config['authors']

    monitors_str = '<tr>' \
                   '<td>{email}</td><td>{day}</td><td>{objectives}</td><td>{authors}</td>' \
                   '</tr>'.format(email=email, day=day, objectives=objectives, authors=authors)

    with open(os.path.join(srcpath, 'templates', 'tracking.html'), 'r') as f:
        tracking_text = f.read()
    target_path = os.path.join(output, 'tracking.html')
    with open(target_path, 'w') as f:
        f.write(tracking_text.format(name=repo_name, nav=compute_nav(home_url, recent_authors, weekly=False),
                                     home=home_url, monthly=home_url, weekly=home_url + 'weekly/',
                                     tracking=home_url + 'tracking.html', monitors=monitors_str))

    if is_today:
        month_start = today - datetime.timedelta(days=14)
        week_start = today - datetime.timedelta(days=7)
        last_month_prs = pr_df[(pr_df.index >= month_start) & (pr_df.index < week_start)]
        last_week_prs = pr_df[pr_df.index >= week_start]
        last_week_commits = commit_df[commit_df.index >= week_start]
        last_mean = last_month_prs.no_reviews.mean()
        this_mean = last_week_prs.no_reviews.mean()
        review_text = 'The mean reviews per pull request was {avg_review_week}, ' \
                      '{status} previous weeks which saw a mean rate of {avg_review_month}'.format(
            avg_review_week=this_mean, avg_review_month=last_mean,
            status='about the same as' if last_mean * 0.9 < this_mean < last_mean * 1.1 else
            'higher than' if this_mean > last_mean else 'lower than'
        )

        with open(os.path.join(srcpath, 'templates', 'summary.html'), 'r') as f:
            page_text = f.read()
        page_text = page_text.format(
            no_prs=last_week_prs.shape[0], no_commits=last_week_commits.shape[0],
            no_lines=last_week_commits.insertions.sum() + last_week_commits.deletions.sum(),
            no_code_lines=last_week_commits.code_changes.sum(),
            review_text=review_text, name=repo_name,
            link=home_url
        )
        subject = 'git-quality weekly summary'
        reporting.email_summary(email, page_text, subject)


@click.command()
@click.option('--directory', required=True, help='Assess quality of the repo at the given path')
@click.option('--output', required=True, help='Save graphs and stats to the given directory')
@click.option('--srcpath')
@click.option('--resume', is_flag=True, help='Load previously saved dataframe, if present')
@click.option('--email', default=None, type=str, help='Email last month\'s summary to this address if set')
@click.option('--authors/--no-authors', default=True)
@click.option('--plotgraphs/--no-plotgraphs', default=True)
def main(directory, output, srcpath='/opt/git-quality', resume=False, email=None, authors=True, plotgraphs=True):
    date_start, date_end = compute_daterange()
    pr_df_orig = fetch_pr_df(date_end, date_start, directory, output, resume)
    commit_df_orig = fetch_commit_df(date_end, date_start, directory, output, resume)

    # copy web template to view them
    home_url = util.read_config('server')['url']
    repo_name = os.path.basename(directory)

    # filter by date
    pr_df = reduce_df(pr_df_orig, date_start, date_end)
    commit_df = reduce_df(commit_df_orig, date_start, date_end)

    # filter for author
    recent_authors = compute_recent_authors(pr_df)

    run_tracking(pr_df_orig, commit_df_orig, srcpath, output, repo_name, home_url, recent_authors)

    with open(os.path.join(srcpath, 'templates', 'index.html'), 'r') as f:
        page_text = f.read()

    os.makedirs(output + '/weekly/', exist_ok=True)
    shutil.copy(os.path.join(srcpath, 'templates', 'styles.css'), os.path.join(output, 'styles.css'))
    target_path = os.path.join(output, 'index.html')
    with open(target_path, 'w') as f:
        f.write(page_text.format(name=repo_name, nav=compute_nav(home_url, recent_authors, weekly=False),
                                 home=home_url, monthly=home_url, weekly=home_url + 'weekly/',
                                 tracking=home_url + 'tracking.html'))

    shutil.copy(os.path.join(srcpath, 'templates', 'styles.css'), os.path.join(output, 'weekly', 'styles.css'))
    target_path = os.path.join(output, 'weekly', 'index.html')
    with open(target_path, 'w') as f:
        f.write(page_text.format(name=repo_name, nav=compute_nav(home_url, recent_authors, weekly=True),
                                 home=home_url, monthly=home_url, weekly=home_url + 'weekly/',
                                 tracking=home_url + 'tracking.html'))

    # plot graphs
    if plotgraphs:
        graphs.plot_pr_stats(pr_df, output, authors=recent_authors, review_authors=recent_authors)
        graphs.plot_commit_stats(commit_df, output, authors=recent_authors)

        graphs.plot_pr_stats(pr_df, output + '/weekly/', authors=recent_authors, review_authors=recent_authors,
                             frequency='W')
        graphs.plot_commit_stats(commit_df, output + '/weekly/', authors=recent_authors, frequency='W')

    if authors:
        for author_name in recent_authors:
            # plot graphs
            directory = os.path.join(output, author_name.replace(' ', '_'))
            os.makedirs(directory, exist_ok=True)
            if plotgraphs:
                graphs.plot_pr_stats(pr_df, directory, authors=[author_name], review_authors=recent_authors,
                                     frequency='M')
                graphs.plot_commit_stats(commit_df, directory, authors=[author_name], frequency='M')

            shutil.copy(os.path.join(srcpath, 'templates', 'styles.css'), os.path.join(directory, 'styles.css'))
            target_path = os.path.join(directory, 'index.html')
            with open(target_path, 'w') as f:
                f.write(page_text.format(name=author_name, nav=compute_nav(home_url, recent_authors, weekly=False),
                                         home=home_url, monthly=home_url + author_name.replace(' ', '_') + '/',
                                         weekly=home_url + 'weekly/' + author_name.replace(' ', '_'),
                                         tracking=home_url + 'tracking.html'))

            directory = os.path.join(output, 'weekly', author_name.replace(' ', '_'))
            os.makedirs(directory, exist_ok=True)
            if plotgraphs:
                graphs.plot_pr_stats(pr_df, directory, authors=[author_name], review_authors=recent_authors,
                                     frequency='W')
                graphs.plot_commit_stats(commit_df, directory, authors=[author_name], frequency='W')

            shutil.copy(os.path.join(srcpath, 'templates', 'styles.css'), os.path.join(directory, 'styles.css'))
            target_path = os.path.join(directory, 'index.html')
            with open(target_path, 'w') as f:
                f.write(page_text.format(name=author_name, nav=compute_nav(home_url, recent_authors, weekly=True),
                                         home=home_url, monthly=home_url + author_name.replace(' ', '_') + '/',
                                         weekly=home_url + 'weekly/' + author_name.replace(' ', '_'),
                                         tracking=home_url + 'tracking.html'))
    # email award winners
    if email:
        metrics_df = compute_awards(pr_df)
        reporting.email_awards(email, metrics_df[:1], repo_name, srcpath=srcpath)


def compute_nav(base_url, recent_authors, weekly=False):
    return ''.join(
        ['<a href="{url}{week_str}{name_ref}/">{name}</a>'.format(name=a, name_ref=a.replace(' ', '_'),
                                                                  url=base_url, week_str='weekly/' if weekly else '')
         for a in recent_authors])


def compute_recent_authors(pr_df):
    date_threshold = pr_df.index.max().to_pydatetime() - datetime.timedelta(days=365 / 3)
    recent_authors = np.sort(pr_df[pr_df.index > date_threshold][gitparser.AUTHOR].unique())
    recent_authors = [ra.strip().replace('\n', '') for ra in recent_authors]
    return recent_authors


def fetch_commit_df(date_end, date_start, directory, output, resume):
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
        os.makedirs(output, exist_ok=True)
        try:
            commit_df.to_csv(results_path)
        except OSError:
            pass
    return commit_df


def fetch_pr_df(date_end, date_start, directory, output, resume):
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
        pr_df = convert_prs_to_dateframe(merges, date_start, date_end)

        # ensure output directory exists
        os.makedirs(output, exist_ok=True)
        try:
            pr_df.to_csv(results_path)
        except OSError:
            pass
    return pr_df


if __name__ == '__main__':
    main()
