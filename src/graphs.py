""" Graphing functions """
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sb

import gitparser
import punchcard


def plot_pr_stats(df, output, authors, review_authors, frequency='M'):
    """ Plots graphs indicating statistics on pull requests and reviews
    :param pd.DataFrame df: dataframe to plot
    :param str output: directory to save plots to
    """
    df = df[df[gitparser.AUTHOR].isin(authors)]
    if df.shape[0] < 1:
        return

    # groupings
    time_grouped_df = df.groupby(pd.Grouper(freq=frequency))
    time_author_grouped_df = df.groupby([pd.Grouper(freq=frequency), gitparser.AUTHOR])
    reviewer_cols = list(df[df.columns.difference(gitparser.PR_COLUMNS)].columns)

    prs_by_author = time_author_grouped_df[gitparser.TITLE].count().unstack(gitparser.AUTHOR).loc[:, authors]
    reviews_by_person = time_grouped_df[reviewer_cols].sum().loc[:, review_authors]

    sb.set_style('darkgrid')

    # overall PR histogram
    pr_df = time_grouped_df[gitparser.AUTHOR].count()
    xticklabels = [dt.strftime("%b'%y") if (i % 3 == 0) else '' for i, dt in enumerate(pr_df.index)]
    fig, ax = plt.subplots(figsize=(7, 4))
    pr_df.plot(colormap='tab10', linewidth=3, ax=ax, kind='bar')
    ax.set_xticklabels(xticklabels, rotation=0)
    ax.set_ylabel('no. pull requests')
    ax.set_title('No. merged pull requests per month')
    plt.gca().set_ylim(bottom=0)
    fig.savefig(os.path.join(output, 'prs.png'), bbox_inches='tight')
    plt.close()

    # avg reviews by month
    reviews_mean = time_grouped_df[gitparser.NO_REVIEWS].mean().as_matrix()
    reviews_std = time_grouped_df[gitparser.NO_REVIEWS].std().as_matrix()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.errorbar(x=pr_df.index, y=reviews_mean, yerr=reviews_std, fmt='o',
                markersize=8, capsize=8)
    ax.set_xticks(pr_df.index)
    ax.set_xticklabels([], minor=1)
    ax.set_xticklabels(xticklabels, rotation=0)
    ax.set_ylabel(gitparser.NO_REVIEWS)
    ax.set_title('Avg reviews per month')
    plt.gca().set_ylim(bottom=0)
    fig.savefig(os.path.join(output, 'avg_reviews.png'), bbox_inches='tight')
    plt.close()

    # authors by month
    authors_df = time_author_grouped_df[gitparser.AUTHOR].size().groupby(level=0).size()
    fig, ax = plt.subplots(figsize=(7, 4))
    authors_df.plot(colormap='tab10', linewidth=2, kind='bar', ax=ax)
    ax.set_xticklabels(xticklabels, rotation=0)
    ax.set_ylabel('no. authors')
    ax.set_title('No. authors per month')
    plt.gca().set_ylim(bottom=0)
    fig.savefig(os.path.join(output, 'authors.png'), bbox_inches='tight')
    plt.close()

    # reviews / author by month
    reviews_author_df = (time_grouped_df[gitparser.NO_REVIEWS].sum() / authors_df)
    fig, ax = plt.subplots(figsize=(7, 4))
    reviews_author_df.plot(colormap='tab10', linewidth=2, ax=ax)
    ax.set_xticks(pr_df.index)
    ax.set_xticklabels(xticklabels, rotation=0)
    ax.set_xticklabels([], minor=1)
    ax.set_ylabel('reviews / authors')
    ax.set_title('Reviews / authors per month')
    plt.gca().set_ylim(bottom=0)
    fig.savefig(os.path.join(output, 'reviews_by_authors.png'), bbox_inches='tight')
    plt.close()

    # PRs by author
    pr_author_df = prs_by_author.fillna(0.)
    fig, ax = plt.subplots(figsize=(7, 4))
    pr_author_df[pr_author_df.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
    ax.set_xticklabels(xticklabels, rotation=0)
    ax.set_ylabel('no. merged pull requests')
    ax.set_title('No. merged pull requests by author per month')
    plt.gca().set_ylim(bottom=1)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc='upper left')
    fig.savefig(os.path.join(output, 'prs_by_author.png'), bbox_inches="tight")
    plt.close()

    # reviews by reviewer
    reviews_df = reviews_by_person.fillna(0.)
    fig, ax = plt.subplots(figsize=(7, 4))
    reviews_df[reviews_df.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
    ax.set_xticklabels(xticklabels, rotation=0)
    ax.set_ylabel('no. reviews')
    ax.set_title('No. reviews by reviewer per month')
    plt.gca().set_ylim(bottom=1)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc='upper left')
    fig.savefig(os.path.join(output, 'reviews_by_reviewer.png'), bbox_inches="tight")
    plt.close()


def plot_commit_stats(df, output, authors, frequency='M'):
    df = df[df[gitparser.AUTHOR].isin(authors)]
    # groupings
    time_grouped_df = df.groupby(pd.Grouper(freq=frequency))
    time_author_grouped_df = df.groupby([pd.Grouper(freq=frequency), gitparser.AUTHOR])
    commit_df = time_grouped_df[gitparser.AUTHOR].count()
    xticklabels = [dt.strftime("%b'%y") if (i % 3 == 0) else '' for i, dt in enumerate(commit_df.index)]
    prs_by_author = time_author_grouped_df[gitparser.TITLE].count().unstack(gitparser.AUTHOR).loc[:, authors]
    pr_author_df = prs_by_author.fillna(0.)
    insertions_by_author = time_author_grouped_df[gitparser.INSERTIONS].sum().unstack(gitparser.AUTHOR).loc[:, authors]
    deletions_by_author = time_author_grouped_df[gitparser.DELETIONS].sum().unstack(gitparser.AUTHOR).loc[:, authors]
    code_files_by_author = time_author_grouped_df[gitparser.CODE_FILES].sum().unstack(gitparser.AUTHOR).loc[:,
                           authors]
    code_changes_by_author = time_author_grouped_df[gitparser.CODE_CHANGES].sum().unstack(gitparser.AUTHOR).loc[:,
                             authors]

    # commits
    fig, ax = plt.subplots(figsize=(7, 4))
    pr_author_df[pr_author_df.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
    ax.set_xticklabels(xticklabels, rotation=0)
    ax.set_ylabel('no. commits')
    ax.set_title('No. commits by author per month')
    plt.gca().set_ylim(bottom=1)
    commit_handles, commit_labels = ax.get_legend_handles_labels()
    ax.legend(commit_handles[::-1], commit_labels[::-1], loc='upper left')
    fig.savefig(os.path.join(output, 'commits_by_author.png'), bbox_inches="tight")
    plt.close()

    # file changes
    insertions_df = insertions_by_author.fillna(0.)
    deletions_df = deletions_by_author.fillna(0.)
    fig, ax = plt.subplots(figsize=(7, 4))
    insertions_df[insertions_df.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
    (-deletions_df / 2).plot.bar(colormap='tab10_r', linewidth=2, ax=ax, stacked=True)
    ax.set_xticklabels(xticklabels, rotation=0)
    ax.set_ylabel('changes')
    ax.set_title('Insertions / deletions by author per month')
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(power_ten_formatter))
    ax.legend(commit_handles[::-1], commit_labels[::-1], loc='upper left')
    fig.savefig(os.path.join(output, 'changes_by_author.png'), bbox_inches="tight")
    plt.close()

    # code files
    code_files_df = code_files_by_author.fillna(0.)
    fig, ax = plt.subplots(figsize=(7, 4))
    code_files_df[code_files_df.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
    ax.set_xticklabels(xticklabels, rotation=0)
    ax.set_ylabel('code files changed')
    ax.set_title('Code files changes by author per month')
    ax.legend(commit_handles[::-1], commit_labels[::-1], loc='upper left')
    fig.savefig(os.path.join(output, 'code_files_by_author.png'), bbox_inches="tight")
    plt.close()

    # code changes
    code_changes_df = code_changes_by_author.fillna(0.)
    fig, ax = plt.subplots(figsize=(7, 4))
    code_changes_df[code_changes_df.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
    ax.set_xticklabels(xticklabels, rotation=0)
    ax.set_ylabel('code lines changed')
    ax.set_title('Code lines changed by author per month')
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(power_ten_formatter))
    ax.legend(commit_handles[::-1], commit_labels[::-1], loc='upper left')
    fig.savefig(os.path.join(output, 'code_changes_by_author.png'), bbox_inches="tight")
    plt.close()

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
    # ax.set_yscale('log')
    ax.set_title('Code changes per commit')
    plt.gca().set_ylim(bottom=0)
    fig.savefig(os.path.join(output, 'commit_changes.png'), bbox_inches='tight')
    plt.close()

    # punch card
    plot = punchcard.plot_punchcard(1000, 400, df.index)
    plot.write_to_png(os.path.join(output, 'punchcard.png'))


def power_ten_formatter(x, pos):
    if x != 0:
        multiplier = x / np.power(10, np.floor(np.log10(np.abs(x))))
        power = int(np.floor(np.log10(np.abs(x))))
        return '${i:0.1f}x10^{n}$'.format(i=multiplier, n=power)
    else:
        return '0'
