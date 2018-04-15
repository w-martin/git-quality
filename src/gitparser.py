""" Functions for parsing git commit messages """
import logging
import re
from functools import partial
from operator import is_not

import numpy as np
from recordclass import recordclass

logger1 = logging.getLogger('git log parser')

# regular expressions for parsing git commit messages (bitbucket merges tested)
commit_regex = re.compile('commit\s([\d\w]{40})\D')
merge_regex = re.compile('[Mm]erge')
pr_regex = re.compile('pull request')
author_regex = re.compile('Author:\s+([\w\s]*\w)\s?[\<\\n]')
date_regex = re.compile('Date:\s+(.*)\n')
pr_title_regex = re.compile('Merged in [\S]+ \(pull request #[\d]+\)\s+((\<[\w+\s]+\>)?[\w\s\d.]*)\s')
squash_title_regex = re.compile('\+[01]{4}\n\s+([\S\s]+)\s+Approved-by')
commit_title_regex = re.compile('\+\d{4}\s*(\S[\S\s.]*)\s*\d+\sfile')
commit_files_regex = re.compile('(\d+)\sfile')
commit_insertions_regex = re.compile('(\d+)\sinsertion')
commit_deletions_regex = re.compile('(\d+)\sdeletion')
code_files_regex = re.compile('\.py\s+\|\s(\d+)\s')
reviewer_regex = re.compile('Approved-by:\s+([\w ]+)')

# indexing constants
HASH = 'commit_hash'
AUTHOR = 'author'
DATE = 'date'
NO_REVIEWS = 'no_reviews'
REVIEWERS = 'reviewers'
TITLE = 'title'
FILES = 'files'
INSERTIONS = 'insertions'
DELETIONS = 'deletions'
CODE_FILES = 'code_files'
CODE_CHANGES = 'code_changes'

# storage for prs
PR_COLUMNS = [HASH, AUTHOR, DATE, TITLE, REVIEWERS, NO_REVIEWS]
pr_structure = recordclass('PullRequest', PR_COLUMNS)
# storage for commits
COMMIT_COLUMNS = [HASH, AUTHOR, DATE, TITLE, FILES, INSERTIONS, DELETIONS, CODE_FILES, CODE_CHANGES]
commit_structure = recordclass('Commit', COMMIT_COLUMNS)


class PullRequest(pr_structure):
    """ Represents a git pull request merge commit """

    def __repr__(self):
        return 'Commit by {author} on {date}, reviewed by {no_reviews}: {title}'.format(
            author=self.author, date=self.date, reviewers=self.no_reviews, title=self.title)


class Commit(commit_structure):
    """ Represents a git commit """

    def __repr__(self):
        return 'Commit by {author} on {date}, ' \
               'files={files}, insertions={insertions}, deletions={deletions}' \
               'code_files={code_files}, code changes={code_changes}'.format(
            author=self.author, date=self.date, title=self.title, files=self.files, insertions=self.insertions,
            deletions=self.deletions, code_files=self.code_files, code_code_changes=self.code_changes)


def parse_pull_requests(commit_hash, text):
    """ Parses the given commit text
    :param str text: the text to parse
    :return: a PullRequest with extracted relevant fields, or None if an error occurred
    :rtype: PullRequest
    """
    try:
        author = author_regex.search(text).group(1)
        date = date_regex.search(text).group(1)
        try:
            title = pr_title_regex.search(text).group(1).strip()
        except AttributeError:
            title = squash_title_regex.search(text).group(1).strip()
        reviewers = [r.strip().replace('\n', '') for r in reviewer_regex.findall(text)]
        # no self reviews allowed in these stats
        try:
            reviewers.remove(author)
        except ValueError:
            pass
        no_reviews = len(reviewers)
        if no_reviews > -1:
            return PullRequest(commit_hash, author, date, title, reviewers, no_reviews)
    except:
        pass
    return None


def parse_commits(commit_hash, text):
    """ Parses the given commit text
    :param str text: the text to parse
    :return: a Commit with extracted relevant fields, or None if an error occurred
    :rtype: PullRequest
    """
    if len(text.strip()) == 0:
        return None
    try:
        if reviewer_regex.search(text) is not None:
            # squash merge
            raise Exception('Squash merge found')

        author = author_regex.search(text).group(1)
        date = date_regex.search(text).group(1)
        title = commit_title_regex.search(text).group(1).strip()
        files = int(commit_files_regex.search(text).group(1).strip())
        try:
            insertions = int(commit_insertions_regex.search(text).group(1).strip())
        except (IndexError, AttributeError):
            insertions = 0
        try:
            deletions = int(commit_deletions_regex.search(text).group(1).strip())
        except (IndexError, AttributeError):
            deletions = 0
        code_change_instances = code_files_regex.findall(text)
        code_files = len(code_change_instances)
        code_changes = int(np.sum([int(fc) for fc in code_change_instances]))
        return Commit(commit_hash, author, date, title, files, insertions, deletions, code_files, code_changes)
    except Exception as e:
        pass
    return None


def extract_pull_requests(commit_log):
    """ Extracts Commits from the given log
    :param str commit_log: the log to extract pull request merge commits from
    :return: a list of pull request merge commits
    :rtype: list[PullRequest]
    """
    commits = commit_regex.split(commit_log)[1:]
    # form tuples of commit hash, log
    commits = list(zip(commits[::2], commits[1::2]))
    logger1.info('Extracted {no_merges} commits'.format(no_merges=len(commits)))
    results = [parse_pull_requests(*c) for c in commits]
    results = list(filter(partial(is_not, None), results))

    logger1.info('Extracted {no_merges} PRs'.format(no_merges=len(results)))

    return results


def regex_extract_variable(text, regex, default=None):
    try:
        return regex.search(text).group(1)
    except AttributeError:
        return default


def extract_commits(log_text):
    commits = commit_regex.split(log_text)[1:]
    # form tuples of commit hash, log
    commits = list(zip(commits[::2], commits[1::2]))
    logger1.info('Extracted {no_commits} commits'.format(no_commits=len(commits)))
    results = [parse_commits(*c) for c in commits]
    results = list(filter(partial(is_not, None), results))

    logger1.info('Extracted {no_commits} commits'.format(no_commits=len(results)))

    return results
