import logging
import os
import re
from collections import namedtuple
from functools import partial
from operator import is_not

import click
import pandas as pd

COMMIT_COLUMNS = ['author', 'date', 'reviewers', 'title']

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
        return 'Commit by {author} on {date}, reviewed by {reviewers}: {title}'.format(
            author=self.author, date=self.date, reviewers=self.reviewers, title=self.title)


def parse_commit(text):
    try:
        author = author_regex.search(text).group(1)
        date = date_regex.search(text).group(1)
        reviewers = reviewer_regex.findall(text)
        title = title_regex.search(text).group(1)
        return Commit(author, date, reviewers, title) if len(reviewers) > 0 else None
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
    result = filter(partial(is_not, None), result)
    return result


def objects_to_dateframe(merges):
    df = pd.DataFrame(merges, columns=COMMIT_COLUMNS)
    # df.set_index(commit_structure).unstack(level=1)
    return df


@click.command()
@click.option('--directory')
def main(directory):
    log_text = get_commit_log(directory)
    merges = get_merges(log_text)
    logging.info("Extracted {no_merges:d} merged pull requests".format(no_merges=len(merges)))

    merge_df = objects_to_dateframe(merges)
    merge_df[['date', 'author']].set_index('date').plot()


if __name__ == '__main__':
    main()
