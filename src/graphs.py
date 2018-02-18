""" Graphing functions """
import itertools
import logging
import os

import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sb

import gitparser
import punchcard


def generate_xtick(i, dt, frequency):
    if 'M' == frequency:
        n = 3
    elif 'W' == frequency:
        n = 9
    else:
        n = 70
    return dt.strftime("%b'%y") if (i % n == 0) else ''


def set_ax_color(ax, textcolor):
    ax.spines['bottom'].set_color(textcolor)
    ax.spines['top'].set_color(textcolor)
    ax.xaxis.label.set_color(textcolor)
    ax.tick_params(axis='x', colors=textcolor)
    ax.spines['left'].set_color(textcolor)
    ax.spines['right'].set_color(textcolor)
    ax.yaxis.label.set_color(textcolor)
    ax.tick_params(axis='y', colors=textcolor)
    ax.title.set_color(textcolor)


def plot_pr_stats(df, output, authors, review_authors, start_date, frequency='M', view_text='Monthly',
                  bgcolor='#FAFAFA', textcolor='#212121'):
    """ Plots graphs indicating statistics on pull requests and reviews
    :param pd.DataFrame df: dataframe to plot
    :param str output: directory to save plots to
    """
    sb.set_style('darkgrid')
    df = df[df[gitparser.AUTHOR].isin(authors)]
    if df.shape[0] < 1:
        return
    freq_str = view_text.lower()[:-2]
    xticks, ranges, xticklabels = generate_xticks(start_date, frequency)

    try:
        # groupings
        time_grouped_df = df.groupby(pd.Grouper(freq=frequency))
        time_author_grouped_df = df.groupby([pd.Grouper(freq=frequency), gitparser.AUTHOR])
        reviewer_cols = list(df[df.columns.difference(gitparser.PR_COLUMNS)].columns)

        prs_by_author = time_author_grouped_df[gitparser.TITLE].count().unstack(gitparser.AUTHOR).loc[:, authors]
        reviews_by_person = time_grouped_df[reviewer_cols].sum().loc[:, review_authors]
    except Exception as e:
        logging.exception(e)
    try:

        # overall PR histogram
        pr_df = time_grouped_df[gitparser.AUTHOR].count()
        fig, ax = plt.subplots(figsize=(7, 4))
        pr_df.plot(colormap='tab10', linewidth=3, ax=ax, kind='bar')
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_ylabel('no. pull requests')
        ax.set_title('No. merged pull requests per {}'.format(freq_str))
        plt.gca().set_ylim(bottom=0)
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'prs.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()
    except Exception as e:
        logging.exception(e)

    try:
        # avg reviews by month
        reviews_mean = time_grouped_df[gitparser.NO_REVIEWS].mean().as_matrix()
        reviews_std = time_grouped_df[gitparser.NO_REVIEWS].std().as_matrix()
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.errorbar(x=pr_df.index, y=reviews_mean, yerr=reviews_std, fmt='o',
                    markersize=8, capsize=8)
        ax.set_xticks(pr_df.index)
        ax.set_xticklabels([], minor=1)
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_xlabel('date')
        ax.set_ylabel(gitparser.NO_REVIEWS)
        ax.set_title('Avg reviews per {}'.format(freq_str))
        plt.gca().set_ylim(bottom=0)
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'avg_reviews.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()
    except Exception as e:
        logging.exception(e)

    try:
        # authors by month
        authors_df = time_author_grouped_df[gitparser.AUTHOR].size().groupby(level=0).size()
        fig, ax = plt.subplots(figsize=(7, 4))
        authors_df.plot(colormap='tab10', linewidth=2, kind='bar', ax=ax)
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_ylabel('no. authors')
        ax.set_title('No. authors per {}'.format(freq_str))
        plt.gca().set_ylim(bottom=0)
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'authors.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()
    except Exception as e:
        logging.exception(e)

    try:
        # PRs by author
        pr_author_df = prs_by_author.fillna(0.)
        fig, ax = plt.subplots(figsize=(7, 4))
        fig.set_facecolor('#444444')
        pr_author_df[pr_author_df.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_ylabel('no. merged pull requests')
        ax.set_title('No. merged pull requests by author per {}'.format(freq_str))
        plt.gca().set_ylim(bottom=1)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc='upper left')
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'prs_by_author.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()
    except Exception as e:
        logging.exception(e)

    try:
        # reviews by reviewer
        reviews_df = reviews_by_person.fillna(0.)
        fig, ax = plt.subplots(figsize=(7, 4))
        reviews_df[reviews_df.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_ylabel('no. reviews')
        ax.set_title('No. reviews by reviewer per {}'.format(freq_str))
        plt.gca().set_ylim(bottom=1)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc='upper left')
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'reviews_by_reviewer.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()

    except Exception as e:
        logging.exception(e)


def plot_commit_stats(df, output, authors, start_date, frequency='M', view_text='Monthly',
                      bgcolor='#FAFAFA', textcolor='#212121'):
    df = df[df[gitparser.AUTHOR].isin(authors)]
    freq_str = view_text.lower()[:-2]
    xticks, ranges, xticklabels = generate_xticks(start_date, frequency)

    try:
        # groupings
        time_grouped_df = df.groupby(pd.Grouper(freq=frequency))
        time_author_grouped_df = df.groupby([pd.Grouper(freq=frequency), gitparser.AUTHOR])
        commit_df = time_grouped_df[gitparser.AUTHOR].count()
        prs_by_author = time_author_grouped_df[gitparser.TITLE].count().unstack(gitparser.AUTHOR).loc[:, authors]
        pr_author_df = prs_by_author.fillna(0.)
        insertions_by_author = time_author_grouped_df[gitparser.INSERTIONS].sum().unstack(gitparser.AUTHOR).loc[:, authors]
        deletions_by_author = time_author_grouped_df[gitparser.DELETIONS].sum().unstack(gitparser.AUTHOR).loc[:, authors]
        code_files_by_author = time_author_grouped_df[gitparser.CODE_FILES].sum().unstack(gitparser.AUTHOR).loc[:,
                               authors]
        code_changes_by_author = time_author_grouped_df[gitparser.CODE_CHANGES].sum().unstack(gitparser.AUTHOR).loc[:,
                                 authors]

    except Exception as e:
        logging.exception(e)
    try:

        # commits
        fig, ax = plt.subplots(figsize=(7, 4))
        pr_author_df[pr_author_df.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_ylabel('no. commits')
        ax.set_title('No. commits by author per {}'.format(freq_str))
        plt.gca().set_ylim(bottom=1)
        commit_handles, commit_labels = ax.get_legend_handles_labels()
        ax.legend(commit_handles[::-1], commit_labels[::-1], loc='upper left')
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'commits_by_author.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()

    except Exception as e:
        logging.exception(e)
    try:

        # file changes
        insertions_df = insertions_by_author.fillna(0.)
        deletions_df = deletions_by_author.fillna(0.)
        fig, ax = plt.subplots(figsize=(7, 4))
        insertions_df[insertions_df.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
        (-deletions_df / 2).plot.bar(colormap='tab10_r', linewidth=2, ax=ax, stacked=True)
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_ylabel('lines changed')
        ax.set_title('Line insertions / deletions by author per {}'.format(freq_str))
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(power_ten_formatter))
        ax.legend(commit_handles[::-1], commit_labels[::-1], loc='upper left')
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'changes_by_author.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()

    except Exception as e:
        logging.exception(e)
    try:

        # code files
        code_files_df = code_files_by_author.fillna(0.)
        fig, ax = plt.subplots(figsize=(7, 4))
        code_files_df[code_files_df.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_ylabel('code files changed')
        ax.set_title('Code files changes by author per {}'.format(freq_str))
        ax.legend(commit_handles[::-1], commit_labels[::-1], loc='upper left')
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'code_files_by_author.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()

    except Exception as e:
        logging.exception(e)
    try:

        # code changes
        code_changes_df = code_changes_by_author.fillna(0.)
        fig, ax = plt.subplots(figsize=(7, 4))
        code_changes_df[code_changes_df.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_ylabel('code lines changed')
        ax.set_title('LOC changed by author per {}'.format(freq_str))
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(power_ten_formatter))
        ax.legend(commit_handles[::-1], commit_labels[::-1], loc='upper left')
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'code_changes_by_author.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()

    except Exception as e:
        logging.exception(e)
    try:

        # avg changes per commit by month
        changes_mean = time_grouped_df[gitparser.CODE_CHANGES].mean().as_matrix()
        changes_std = time_grouped_df[gitparser.CODE_CHANGES].std().as_matrix()
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.errorbar(x=commit_df.index, y=changes_mean, yerr=changes_std, fmt='o',
                    markersize=8, capsize=8)
        # sb.violinplot(x=frequency, y=gitparser.CODE_CHANGES, data=df, ax=ax, color=plt.cm.tab20c(1), cut=0)
        ax.set_xticks(commit_df.index)
        ax.set_xticklabels([], minor=1)
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_ylabel(gitparser.CODE_CHANGES)
        ax.set_xlabel('date')
        # ax.set_yscale('log')
        ax.set_title('Average LOC changed per commit')
        ax.set_ylabel('code lines changed')
        plt.gca().set_ylim(bottom=0)
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'commit_changes.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()

    except Exception as e:
        logging.exception(e)

    # punch card
    plot = punchcard.plot_punchcard(1000, 400, df.index)
    plot.write_to_png(os.path.join(output, 'punchcard.png'))


def compute_next_month(d):
    next_d = d - datetime.timedelta(weeks=4)
    next_d = datetime.datetime(next_d.year, next_d.month, 1)
    return next_d


def generate_xticks(start_date, frequency):
    ticks = []
    d = datetime.datetime.today()
    if frequency == 'M':
        compute_next_date = compute_next_month
    elif frequency == 'W':
        compute_next_date = lambda x: x - datetime.timedelta(days=7)
    elif frequency == 'D':
        compute_next_date = lambda x: x - datetime.timedelta(days=1)
    else:
        raise NotImplementedError('Not implemented for frequency {}'.format(frequency))

    while d > start_date:
        ticks += [d]
        d = compute_next_date(d)
    ticks += [d]
    ticks = ticks[::-1]
    ranges = list(zip(ticks[:-1], ticks[1:]))
    ticks = ticks[1:]
    tick_labels = [generate_xtick(i, d, frequency) for i, d in enumerate(ticks)]
    return ticks, ranges, tick_labels


def power_ten_formatter(x, pos):
    if x != 0:
        multiplier = x / np.power(10, np.floor(np.log10(np.abs(x))))
        power = int(np.floor(np.log10(np.abs(x))))
        return '${i:0.1f}x10^{n}$'.format(i=multiplier, n=power)
    else:
        return '0'
