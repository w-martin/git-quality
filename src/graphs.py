""" Graphing functions """
import datetime
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sb

import gitparser
import punchcard


def plot_pr_stats(df, output, authors):
    """ Plots graphs indicating statistics on pull requests and reviews
    :param pd.DataFrame df: dataframe to plot
    :param str output: directory to save plots to
    """
    # groupings
    time_grouped_df = df.groupby(pd.Grouper(freq='M'))
    time_author_grouped_df = df.groupby([pd.Grouper(freq='M'), gitparser.AUTHOR])
    reviewer_cols = list(df[df.columns.difference(gitparser.PR_COLUMNS)].columns)

    prs_by_author = time_author_grouped_df[gitparser.TITLE].count().unstack(gitparser.AUTHOR).loc[:, authors]
    reviews_by_person = time_grouped_df[reviewer_cols].sum().loc[:, authors]

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


def plot_commit_stats(df, output, authors):
    df.sort_index(inplace=True)

    # groupings
    time_grouped_df = df.groupby(pd.Grouper(freq='M'))
    time_author_grouped_df = df.groupby([pd.Grouper(freq='M'), gitparser.AUTHOR])
    pr_df = time_grouped_df[gitparser.AUTHOR].count()
    xticklabels = [dt.strftime("%b'%y") if (i % 3 == 0) else '' for i, dt in enumerate(pr_df.index)]
    prs_by_author = time_author_grouped_df[gitparser.TITLE].count().unstack(gitparser.AUTHOR).loc[:, authors]
    pr_author_df = prs_by_author.fillna(0.)
    fig, ax = plt.subplots(figsize=(7, 4))
    pr_author_df[pr_author_df.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
    ax.set_xticklabels(xticklabels, rotation=0)
    ax.set_ylabel('no. merged pull requests')
    ax.set_title('No. merged pull requests by author per month')
    plt.gca().set_ylim(bottom=1)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc='upper left')
    fig.savefig(os.path.join(output, 'commits_by_author.png'), bbox_inches="tight")
    plt.close()

    # punch card
    plot = punchcard.plot_punchcard(1000, 400, df.index)
    plot.write_to_png(os.path.join(output, 'punchcard.png'))
