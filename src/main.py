""" Main entry point """
import logging
import os
import shutil
from contextlib import contextmanager

import click
import pandas as pd
import sklearn.preprocessing

import gitparser
import graphs
import reporting

logging.basicConfig(level=logging.INFO)

# temporarily save the git log to this file and delete it afterwards
GITLOG_FILENAME = 'git_merges.log'


@contextmanager
def cd(directory):
    current_dir = os.getcwd()
    os.chdir(directory)
    yield
    os.chdir(current_dir)


def load_commit_log():
    """ Loads the commit log from the given directory
    :param str directory: the directory to load the commit log from
    :return: the commit log
    :rtype: str
    """
    os.system('git log --use-mailmap --merges > {log_filename}'.format(log_filename=GITLOG_FILENAME))
    with open(GITLOG_FILENAME, 'r') as f:
        result = f.read()
    os.remove(GITLOG_FILENAME)
    logging.info('Fetched commit log')
    return result


def convert_commits_to_dateframe(commits):
    """ Converts a list of Commits to a pandas dataframe indexed by date
    :param list[gitparser.Commit] commits: the list of commits to convert
    :return: a pandas dataframe with a row per commit
    :rtype: pd.DataFrame
    """
    df = pd.DataFrame(commits, columns=gitparser.COMMIT_COLUMNS)
    # handle date
    df[gitparser.DATE] = pd.to_datetime(df[gitparser.DATE], errors='coerce')
    df.set_index([gitparser.DATE], inplace=True)
    # one hot columns for reviewers
    mlb = sklearn.preprocessing.MultiLabelBinarizer()
    df = df.join(pd.DataFrame(mlb.fit_transform(df.pop(gitparser.REVIEWERS)),
                              columns=mlb.classes_, index=df.index))
    return df


@click.command()
@click.option('--directory', required=True, help='Assess quality of the repo at the given path')
@click.option('--output', required=True, help='Save graphs and stats to the given directory')
@click.option('--srcpath')
@click.option('--resume', is_flag=True, help='Load previously saved dataframe, if present')
@click.option('--email', default=None, type=str, help='Email last month\'s summary to this address if set')
def main(directory, output, srcpath='/opt/git-quality', resume=False, email=None):

    results_path = os.path.join(output, 'merge_results.csv')
    merge_df = None
    if resume:
        try:
            merge_df = pd.DataFrame.from_csv(results_path)
        except OSError:
            pass

    if merge_df is None:
        # load the git log and parse it
        merges = []
        for d in directory.split(','):
            with cd(d):
                log_text = load_commit_log()
                pr_commits = gitparser.extract_pr_commits(log_text)

                merges += pr_commits

        logging.info("Extracted {no_merges:d} merged pull requests".format(no_merges=len(merges)))

        # convert to pandas dataframe
        merge_df = convert_commits_to_dateframe(merges)

        # ensure output directory exists
        output = os.path.abspath(output)
        try:
            os.makedirs(output)
        except OSError:
            pass
        try:
            merge_df.to_csv(results_path)
        except OSError:
            pass

    # now plot some nice graphs
    metrics_df = graphs.plot_review_stats(merge_df, output)
    repo_name = os.path.basename(directory)
    # email award winners
    if email:
        reporting.email_awards(email, metrics_df[:1], repo_name, srcpath=srcpath)
    # copy web template to view them
    target_path = os.path.join(output, 'index.html')
    shutil.copyfile(os.path.join(srcpath, 'templates', 'index.html'), target_path)
    os.system('sed -i s/{name}/%s/g %s' % (repo_name, target_path))


if __name__ == '__main__':
    main()
