""" Main entry point """
import logging
import os

import click
import pandas as pd

import gitparser
import graphs

logging.basicConfig(level=logging.INFO)

# temporarily save the git log to this file and delete it afterwards
GITLOG_FILENAME = 'aed.log'


def load_commit_log(directory):
    """ Loads the commit log from the given directory
    :param str directory: the directory to load the commit log from
    :return: the commit log
    :rtype: str
    """
    current_dir = os.getcwd()
    os.chdir(directory)
    os.system('git log --use-mailmap --merges > {log_filename}'.format(log_filename=GITLOG_FILENAME))
    with open(GITLOG_FILENAME, 'r') as f:
        result = f.read()
    os.remove(GITLOG_FILENAME)
    os.chdir(current_dir)
    return result


def convert_commits_to_dateframe(commits):
    """ Converts a list of Commits to a pandas dataframe indexed by date
    :param list[gitparser.Commit] commits: the list of commits to convert
    :return: a pandas dataframe with a row per commit
    :rtype: pd.DataFrame
    """
    df = pd.DataFrame(commits, columns=gitparser.COMMIT_COLUMNS)
    df[gitparser.DATE] = pd.to_datetime(df[gitparser.DATE], errors='coerce')
    df.set_index([gitparser.DATE], inplace=True)
    return df


@click.command()
@click.option('--directory', required=True, help='Assess quality of the repo at the given path')
@click.option('--output', required=True, help='Save graphs and stats to the given directory')
def main(directory, output):
    # load the git log and parse it
    log_text = load_commit_log(directory)
    merges = gitparser.extract_pr_commits(log_text)
    logging.info("Extracted {no_merges:d} merged pull requests".format(no_merges=len(merges)))

    # convert to pandas dataframe
    merge_df = convert_commits_to_dateframe(merges)

    # ensure output directory exists
    output = os.path.abspath(output)
    try:
        os.makedirs(output)
    except OSError:
        pass

    # now plot some nice graphs
    graphs.plot_review_stats(merge_df, output)


if __name__ == '__main__':
    main()
