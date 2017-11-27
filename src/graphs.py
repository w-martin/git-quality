""" Graphing functions """
import os

import matplotlib.pyplot as plt
import pandas as pd

import gitparser


def plot_review_stats(df, output):
    """ Plots graphs indicating statistics on pull requests and reviews
    :param pd.DataFrame df: dataframe to plot
    :param str output: directory to save plots to
    """
    # groupings
    time_grouped_df = df.groupby(pd.TimeGrouper(freq='M'))
    time_author_grouped_df = df.groupby([pd.TimeGrouper(freq='M'), gitparser.AUTHOR])
    reviewer_cols = list(df[df.columns.difference(gitparser.COMMIT_COLUMNS)].columns)

    # overall PR histogram
    ax = time_grouped_df[gitparser.AUTHOR].count().plot()
    ax.set_ylabel('no. merged pull requests')
    ax.set_title('No. merged pull requests per month')
    plt.gca().set_ylim(bottom=0)
    ax.get_figure().savefig(os.path.join(output, 'prs.png'))
    plt.close()

    # PRs by author
    prs_by_author = time_author_grouped_df.count()[gitparser.TITLE].unstack(gitparser.AUTHOR)
    ax = prs_by_author.fillna(0.).plot()
    ax.set_ylabel('no. merged pull requests')
    ax.set_title('No. merged pull requests by author per month')
    plt.gca().set_ylim(bottom=-1)
    lgd = ax.legend(loc=9, bbox_to_anchor=(1.6, 1.0))
    ax.get_figure().savefig(os.path.join(output, 'prs_by_author.png'),
                            additional_artists=[lgd], bbox_inches="tight")
    plt.close()

    # reviews by reviewer
    reviews_by_person = time_grouped_df[reviewer_cols].sum()
    ax = reviews_by_person.fillna(0.).plot()
    ax.set_ylabel('no. reviews')
    ax.set_title('No. reviews by reviewer per month')
    plt.gca().set_ylim(bottom=-1)
    lgd = ax.legend(loc=9, bbox_to_anchor=(1.6, 1.0))
    ax.get_figure().savefig(os.path.join(output, 'reviews_by_reviewer.png'),
                            additional_artists=[lgd], bbox_inches="tight")
    plt.close()

    # reviews / PRs by author
    ax = (reviews_by_person / prs_by_author).dropna(axis=1, how="all").plot()
    ax.set_ylabel('reviews / prs')
    ax.set_title('Reviews / PRs by author per month')
    plt.gca().set_ylim(bottom=-1)
    lgd = ax.legend(loc=9, bbox_to_anchor=(1.6, 1.0))
    ax.get_figure().savefig(os.path.join(output, 'reviews_over_prs.png'),
                            additional_artists=[lgd], bbox_inches="tight")
    plt.close()

    # avg reviews by month
    ax = time_grouped_df[gitparser.NO_REVIEWS].mean().plot()
    ax.set_ylabel(gitparser.NO_REVIEWS)
    ax.set_title('Avg reviews per month')
    plt.gca().set_ylim(bottom=0)
    ax.get_figure().savefig(os.path.join(output, 'avg_reviews.png'))
    plt.close()

    # authors by month
    ax = time_author_grouped_df[gitparser.AUTHOR].size().groupby(level=0).size().plot()
    ax.set_ylabel('no. authors')
    ax.set_title('No. authors per month')
    plt.gca().set_ylim(bottom=0)
    ax.get_figure().savefig(os.path.join(output, 'authors.png'))
    plt.close()

    # reviews / author by month
    ax = (time_grouped_df[gitparser.NO_REVIEWS].sum() /
          time_author_grouped_df[gitparser.AUTHOR].size().groupby(level=0).size()).plot()
    ax.set_ylabel('reviews / authors')
    ax.set_title('Reviews / authors per month')
    plt.gca().set_ylim(bottom=0)
    ax.get_figure().savefig(os.path.join(output, 'reviews_by_authors.png'))
    plt.close()
