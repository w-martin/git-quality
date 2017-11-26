import re
from collections import namedtuple
from functools import partial
from operator import is_not

# regular expressions for parsing git commit messages
merge_regex = re.compile('commit (\S){40}\\n')
author_regex = re.compile('Author:\s+(.*)\\n')
date_regex = re.compile('Date:\s+(.*)\\n')
reviewer_regex = re.compile('Approved-by:\s+(\w+ \w+ <[\w\d]+.?[\w\d]+@[\w\d]+.[\w\d]+>)')
title_regex = re.compile('Merged in [\w/-]+ \(pull request #[\d]+\)\\n\s+\\n\s+([\w\s\d]*)\\n')

COMMIT_COLUMNS = ['author', 'date', 'reviewers', 'title', 'no_reviews']
commit_structure = namedtuple('Commit', COMMIT_COLUMNS)


class Commit(commit_structure):
    """ Represents a git pull request merge commit """
    def __repr__(self):
        return 'Commit by {author} on {date}, reviewed by {no_reviews}: {title}'.format(
            author=self.author, date=self.date, reviewers=self.no_reviews, title=self.title)


def parse_commit(text):
    """ Parses the given commit text
    :param str text: the text to parse
    :return: a Commit with extracted relevant fields, or None if an error occurred
    :rtype: Commit
    """
    try:
        author = author_regex.search(text).group(1)
        date = date_regex.search(text).group(1)
        reviewers = reviewer_regex.findall(text)
        title = title_regex.search(text).group(1)
        no_reviews = len(reviewers)
        return Commit(author, date, reviewers, title, no_reviews) if no_reviews > 0 else None
    except:
        return None


def extract_pr_commits(commit_log):
    """ Extracts Commits from the given log
    :param str commit_log: the log to extract pull request merge commits from
    :return: a list of pull request merge commits
    :rtype: list[Commit]
    """
    results = [parse_commit(c) for c in merge_regex.split(commit_log)]
    results = list(filter(partial(is_not, None), results))
    return results
