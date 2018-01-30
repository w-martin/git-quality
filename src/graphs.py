""" Graphing functions """
import datetime
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sb

import gitparser


def plot_review_stats(df, output):
    """ Plots graphs indicating statistics on pull requests and reviews
    :param pd.DataFrame df: dataframe to plot
    :param str output: directory to save plots to
    """
    df.sort_index(inplace=True)
    df['month'] = df.index.strftime("%b'%y")
    df['week'] = df.index.strftime("%b'%U'%y")
    # filters
    date_threshold = df.index.max().to_pydatetime() - datetime.timedelta(days=365 / 3)
    recent_authors = np.sort(df[df.index > date_threshold][gitparser.AUTHOR].unique())

    # groupings
    time_grouped_df = df.groupby(pd.Grouper(freq='M'))
    time_author_grouped_df = df.groupby([pd.Grouper(freq='M'), gitparser.AUTHOR])
    reviewer_cols = list(df[df.columns.difference(gitparser.COMMIT_COLUMNS)].columns)

    prs_by_author = time_author_grouped_df[gitparser.TITLE].count().unstack(gitparser.AUTHOR).loc[:, recent_authors]
    reviews_by_person = time_grouped_df[reviewer_cols].sum().loc[:, recent_authors]

    sb.set_style('darkgrid')

    # overall PR histogram
    pr_df = time_grouped_df[gitparser.AUTHOR].count()[:-1]
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
    df['month'] = df.index.strftime("%b'%y")

    fig, ax = plt.subplots(figsize=(7, 4))
    # sb.violinplot(x=)
    sb.violinplot(x='month', y=gitparser.NO_REVIEWS, data=df, ax=ax)
    # ax.set_xticks(pr_df.index)
    # ax.set_xticklabels([], minor=1)
    ax.set_xticklabels(xticklabels, rotation=0)
    ax.set_ylabel(gitparser.NO_REVIEWS)
    ax.set_title('Avg reviews per month')
    plt.gca().set_ylim(bottom=0)
    fig.savefig(os.path.join(output, 'avg_reviews.png'), bbox_inches='tight')
    plt.close()

    # authors by month
    authors_df = time_author_grouped_df[gitparser.AUTHOR].size().groupby(level=0).size()[:-1]
    fig, ax = plt.subplots(figsize=(7, 4))
    authors_df.plot(colormap='tab10', linewidth=2, kind='bar', ax=ax)
    ax.set_xticklabels(xticklabels, rotation=0)
    ax.set_ylabel('no. authors')
    ax.set_title('No. authors per month')
    plt.gca().set_ylim(bottom=0)
    fig.savefig(os.path.join(output, 'authors.png'), bbox_inches='tight')
    plt.close()

    # reviews / author by month
    reviews_author_df = (time_grouped_df[gitparser.NO_REVIEWS].sum() / authors_df)[:-1]
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
    pr_author_df = prs_by_author.fillna(0.)[:-1]
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
    reviews_df = reviews_by_person.fillna(0.)[:-1]
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
