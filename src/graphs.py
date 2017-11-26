""" Graphing functions """
import os

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
    time_reviews_grouped_df = df.groupby([pd.TimeGrouper(freq='M'), gitparser.NO_REVIEWS])

    # overall PR histogram
    ax = time_grouped_df[gitparser.AUTHOR].count().plot()
    ax.set_ylabel('no merged pull requests')
    ax.set_title('No merged pull requests by month')
    ax.get_figure().savefig(os.path.join(output, 'prs.png'))

    # PRs by author
    ax = time_author_grouped_df.count()[gitparser.TITLE].unstack(gitparser.AUTHOR).plot()
    ax.set_ylabel('no merged pull requests')
    ax.set_title('No merged pull requests by author by month')
    ax.get_figure().savefig(os.path.join(output, 'prs_by_author.png'))

    # avg reviews by month
    ax = time_grouped_df[gitparser.NO_REVIEWS].mean().plot()
    ax.set_ylabel(gitparser.NO_REVIEWS)
    ax.set_title('Avg reviews by month')
    ax.get_figure().savefig(os.path.join(output, 'avg_reviews.png'))

    # authors by month
    ax = time_author_grouped_df[gitparser.AUTHOR].size().groupby(level=0).size().plot()
    ax.set_ylabel('no authors')
    ax.set_title('No authors by month')
    ax.get_figure().savefig(os.path.join(output, 'authors.png'))

    # avg reviews / author by month
    ax = (time_grouped_df[gitparser.NO_REVIEWS].mean() /
          time_reviews_grouped_df[gitparser.NO_REVIEWS].size().groupby(
              level=0).size()).plot()
    ax.set_ylabel('avg reviews / no authors')
    ax.set_title('Average reviews / no authors by month')
    ax.get_figure().savefig(os.path.join(output, 'avg_reviews_by_authors.png'))

    # total reviews / author by month
    (time_grouped_df[gitparser.NO_REVIEWS].sum() /
     time_reviews_grouped_df[gitparser.NO_REVIEWS].size().groupby(level=0).size()).plot()
    ax.set_ylabel('total reviews / authors')
    ax.set_title('Total reviews / authors by month')
    ax.get_figure().savefig(os.path.join(output, 'total_reviews_by_authors.png'))
