import logging
import os

import click
import pandas as pd

import gitparser

logging.basicConfig(level=logging.INFO)

# temporarily save the git log to this file and delete it afterwards
LOG_FILENAME = 'aed.log'


def load_commit_log(directory):
    """ Loads the commit log from the given directory
    :param str directory: the directory to load the commit log from
    :return: the commit log
    :rtype: str
    """
    current_dir = os.getcwd()
    os.chdir(directory)
    os.system('git log --use-mailmap --merges > {log_filename}'.format(log_filename=LOG_FILENAME))
    with open(LOG_FILENAME, 'r') as f:
        result = f.read()
    os.remove(LOG_FILENAME)
    os.chdir(current_dir)
    return result


def convert_commits_to_dateframe(commits):
    """ Converts a list of Commits to a pandas dataframe indexed by date
    :param list[gitparser.Commit] commits: the list of commits to convert
    :return: a pandas dataframe with a row per commit
    :rtype: pd.DataFrame
    """
    df = pd.DataFrame(commits, columns=gitparser.COMMIT_COLUMNS)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
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
    merge_df.set_index(['date'], inplace=True)
    time_grouped_df = merge_df.groupby(pd.TimeGrouper(freq='M'))

    # ensure output directory exists
    output = os.path.abspath(output)
    try:
        os.makedirs(output)
    except OSError:
        pass

    # overall PR histogram
    ax = time_grouped_df['author'].count().plot()
    ax.set_ylabel('no merged pull requests')
    ax.set_title('No merged pull requests by month')
    ax.get_figure().savefig(os.path.join(output, 'prs.png'))

    # PRs by author
    ax = merge_df.groupby([pd.TimeGrouper(freq='M'), 'author']).count()['title'].unstack('author').plot()
    ax.set_ylabel('no merged pull requests')
    ax.set_title('No merged pull requests by author by month')
    ax.get_figure().savefig(os.path.join(output, 'prs_by_author.png'))

    # avg reviews by month
    ax = time_grouped_df['no_reviews'].mean().plot()
    ax.set_ylabel('no_reviews')
    ax.set_title('Avg reviews by month')
    ax.get_figure().savefig(os.path.join(output, 'avg_reviews.png'))

    # authors by month
    ax = merge_df.groupby([pd.TimeGrouper(freq='M'), 'author'])['author'].size().groupby(level=0).size().plot()
    ax.set_ylabel('no authors')
    ax.set_title('No authors by month')
    ax.get_figure().savefig(os.path.join(output, 'authors.png'))

    # avg reviews / author by month
    ax = (time_grouped_df['no_reviews'].mean() /
          merge_df.groupby([pd.TimeGrouper(freq='M'), 'no_reviews'])['no_reviews'].size().groupby(
              level=0).size()).plot()
    ax.set_ylabel('avg reviews / no authors')
    ax.set_title('Average reviews / no authors by month')
    ax.get_figure().savefig(os.path.join(output, 'avg_reviews_by_authors.png'))

    # total reviews / author by month
    (time_grouped_df['no_reviews'].sum() /
     merge_df.groupby([pd.TimeGrouper(freq='M'), 'no_reviews'])['no_reviews'].size().groupby(level=0).size()).plot()
    ax.set_ylabel('total reviews / authors')
    ax.set_title('Total reviews / authors by month')
    ax.get_figure().savefig(os.path.join(output, 'total_reviews_by_authors.png'))


if __name__ == '__main__':
    main()
