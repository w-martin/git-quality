""" Functions for parsing git commit messages """
import logging
import re
from recordclass import recordclass
from functools import partial
from operator import is_not

logger1 = logging.getLogger('git log parser')

# regular expressions for parsing git commit messages (bitbucket merges tested)
commit_regex = re.compile('commit\s(\S+)\s')
merge_regex = re.compile('[Mm]erge')
pr_regex = re.compile('pull request')
author_regex = re.compile('Author:\s+([\w\s]*\w)\s?[\<\\n]')
date_regex = re.compile('Date:\s+(.*)\n')
title_regex = re.compile('Merged in [\S]+ \(pull request #[\d]+\)\s+((\<[\w+\s]+\>)?[\w\s\d.]*)\s')
reviewer_regex = re.compile('Approved-by:\s+([\w ]+)')
files_regex = re.compile('(\d+)\sfile')
insertions_regex = re.compile('(\d+)\sinsertion')
deletions_regex = re.compile('(\d+)\sdeletion')

# indexing constants
HASH = 'commit_hash'
AUTHOR = 'author'
DATE = 'date'
NO_REVIEWS = 'no_reviews'
REVIEWERS = 'reviewers'
TITLE = 'title'
FILES = 'files_changed'
INSERTIONS = 'insertions'
DELETIONS = 'deletions'
CHANGES = 'changes'

# storage for commits
COMMIT_COLUMNS = [HASH, AUTHOR, DATE, TITLE, REVIEWERS, NO_REVIEWS, FILES, INSERTIONS, DELETIONS, CHANGES]
commit_structure = recordclass('Commit', COMMIT_COLUMNS)


class Commit(commit_structure):
    """ Represents a git pull request merge commit """

    def __repr__(self):
        return 'Commit by {author} on {date}, reviewed by {no_reviews}: {title}'.format(
            author=self.author, date=self.date, reviewers=self.no_reviews, title=self.title)


def parse_pr_commit(commit_hash, text):
    """ Parses the given commit text
    :param str text: the text to parse
    :return: a Commit with extracted relevant fields, or None if an error occurred
    :rtype: Commit
    """
    try:
        author = author_regex.search(text).group(1)
        date = date_regex.search(text).group(1)
        title = title_regex.search(text).group(1).strip()
        reviewers = [r.strip().replace('\n', '') for r in reviewer_regex.findall(text)]
        # no self reviews allowed in these stats
        try:
            reviewers.remove(author)
        except ValueError:
            pass
        no_reviews = len(reviewers)
        if no_reviews > -1:
            return Commit(commit_hash, author, date, title, reviewers, no_reviews, 0, 0, 0, 0)
    except:
        pass
    return None


def extract_pr_commits(commit_log):
    """ Extracts Commits from the given log
    :param str commit_log: the log to extract pull request merge commits from
    :return: a list of pull request merge commits
    :rtype: list[Commit]
    """
    commits = commit_regex.split(commit_log)[1:]
    # form tuples of commit hash, log
    commits = list(zip(commits[::2], commits[1::2]))
    logger1.info('Extracted {no_merges} merges'.format(no_merges=len(commits)))
    results = [parse_pr_commit(*c) for c in commits]
    results = list(filter(partial(is_not, None), results))

    logger1.info('Extracted {no_merges} PRs'.format(no_merges=len(results)))

    return results


def parse_commit_for_changes(text):
    no_files = int(regex_extract_variable(text, files_regex, 0))
    insertions = int(regex_extract_variable(text, insertions_regex, 0))
    deletions = int(regex_extract_variable(text, deletions_regex, 0))
    return no_files, insertions, deletions


def regex_extract_variable(text, regex, default=None):
    try:
        return regex.search(text).group(1)
    except AttributeError:
        return default
