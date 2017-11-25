import os
from functools import partial
from operator import is_not

import click
import re

LOG_FILENAME = 'aed.log'
merge_regex = re.compile('commit (\S){40}\\n')
author_regex = re.compile('Author:\s+(.*)\\n')
date_regex = re.compile('Date:\s+(.*)\\n')
reviewer_regex = re.compile('Approved-by:\s+(\w+ \w+ <[\w\d]+.?[\w\d]+@[\w\d]+.[\w\d]+>)')
title_regex = re.compile('Merged in [\w/-]+ \(pull request #[\d]+\)\\n\s+\\n\s+([\w\s\d]*)\\n')


class Commit(object):
    author = ''
    date = ''
    reviewers = ''
    title = ''

    def __init__(self, author, date, reviewers, title):
        self.author = author
        self.date = date
        self.reviewers = reviewers
        self.title = title

    def __repr__(self):
        return 'Commit by {author} on {date}, reviewed by {reviewers}: {title}'.format(
            author=self.author, date=self.date, reviewers=self.reviewers, title=self.title)


def parse_commit(text):
        try:
            author = author_regex.search(text).group(1)
            date = date_regex.search(text).group(1)
            reviewers = reviewer_regex.findall(text)
            title = title_regex.search(text).group(1)
            return Commit(author, date, reviewers, title)
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


@click.command()
@click.option('--directory')
def main(directory):
    log_text = get_commit_log(directory)
    merges = get_merges(log_text)
    i = 10

if __name__ == '__main__':
    main()
