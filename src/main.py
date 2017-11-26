import logging
import os
import re
from collections import namedtuple
from functools import partial
from operator import is_not

import click
import pandas as pd

COMMIT_COLUMNS = ['author', 'date', 'reviewers', 'title', 'no_reviews']

logging.basicConfig(level=logging.INFO)

LOG_FILENAME = 'aed.log'
merge_regex = re.compile('commit (\S){40}\\n')
author_regex = re.compile('Author:\s+(.*)\\n')
date_regex = re.compile('Date:\s+(.*)\\n')
reviewer_regex = re.compile('Approved-by:\s+(\w+ \w+ <[\w\d]+.?[\w\d]+@[\w\d]+.[\w\d]+>)')
title_regex = re.compile('Merged in [\w/-]+ \(pull request #[\d]+\)\\n\s+\\n\s+([\w\s\d]*)\\n')

commit_structure = namedtuple('Commit', COMMIT_COLUMNS)


class Commit(commit_structure):
    def __repr__(self):
        return 'Commit by {author} on {date}, reviewed by {no_reviews}: {title}'.format(
            author=self.author, date=self.date, reviewers=self.no_reviews, title=self.title)


def parse_commit(text):
    try:
        author = author_regex.search(text).group(1)
        date = date_regex.search(text).group(1)
        reviewers = reviewer_regex.findall(text)
        title = title_regex.search(text).group(1)
        no_reviews = len(reviewers)
        return Commit(author, date, reviewers, title, no_reviews) if no_reviews > 0 else None
    except:
        return None


def get_commit_log(directory):
    current_dir = os.getcwd()
    os.chdir(directory)
    os.system('git log --use-mailmap --merges > {log_filename}'.format(log_filename=LOG_FILENAME))
    with open(LOG_FILENAME, 'r') as f:
        result = f.read()
    os.remove(LOG_FILENAME)
    os.chdir(current_dir)
    return result


def get_merges(commit_log):
    result = [parse_commit(c) for c in merge_regex.split(commit_log)]
    result = list(filter(partial(is_not, None), result))
    return result


def objects_to_dateframe(merges):
    df = pd.DataFrame(merges, columns=COMMIT_COLUMNS)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    # df.set_index(commit_structure).unstack(level=1)
    return df


@click.command()
@click.option('--directory', required=True, help='Assess quality of the repo at the given path')
@click.option('--output', required=True, help='Save graphs and stats to the given directory')
def main(directory, output):
    log_text = get_commit_log(directory)
    merges = get_merges(log_text)
    logging.info("Extracted {no_merges:d} merged pull requests".format(no_merges=len(merges)))

    output = os.path.abspath(output)
    try:
        os.makedirs(output)
    except OSError:
        pass

    # convert to pandas dataframe
    merge_df = objects_to_dateframe(merges)
    merge_df.set_index(['date'], inplace=True)
    time_grouped_df = merge_df.groupby(pd.TimeGrouper(freq='M'))

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
          merge_df.groupby([pd.TimeGrouper(freq='M'), 'no_reviews'])['no_reviews'].size().groupby(level=0).size()).plot()
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
