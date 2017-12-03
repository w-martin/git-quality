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


def fetch_commit_stats(commit_hash):
    command = 'git diff --shortstat -w {hash}^ {hash} > {log_filename}'.format(
        hash=commit_hash, log_filename=GITLOG_FILENAME)
    os.system(command)
    with open(GITLOG_FILENAME, 'r') as f:
        result = f.read()
    os.remove(GITLOG_FILENAME)
    no_files, lines_added, lines_deleted = gitparser.parse_commit_for_changes(result)
    return no_files, lines_added, lines_deleted


def set_commit_stats(commit):
    commit_hash = commit.__getattribute__(gitparser.HASH)
    no_files, lines_added, lines_deleted = fetch_commit_stats(commit_hash)
    commit.__setattr__(gitparser.FILES, no_files)
    commit.__setattr__(gitparser.INSERTIONS, lines_added)
    commit.__setattr__(gitparser.DELETIONS, lines_deleted)


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
    # changes
    df.changes = df.insertions + df.deletions
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
def main(directory, output, srcpath='/opt/git-quality', resume=False):

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

                # get info for files, lines added and deleted
                for pr in pr_commits:
                    set_commit_stats(pr)

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
    graphs.plot_review_stats(merge_df, output)
    # copy web template to view them
    repo_name = os.path.basename(directory)
    target_path = os.path.join(output, 'index.html')
    shutil.copyfile(os.path.join(srcpath, 'templates', 'index.html'), target_path)
    os.system('sed -i s/{name}/%s/g %s' % (repo_name, target_path))


if __name__ == '__main__':
    main()
