""" Graphing functions """
import calendar
import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sb

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

    prs_by_author = time_author_grouped_df[gitparser.TITLE].count().unstack(gitparser.AUTHOR)
    reviews_by_person = time_grouped_df[reviewer_cols].sum()
    reviews_received_by_author = time_author_grouped_df[gitparser.NO_REVIEWS].sum().unstack(gitparser.AUTHOR)

    # metrics
    harmless = prs_by_author.idxmin(axis=1)
    bookworm = reviews_by_person.idxmax(axis=1)
    shakespear = reviews_received_by_author.idxmax(axis=1)
    tldr = reviews_by_person[reviews_by_person > 1].idxmin(axis=1)
    metrics_df = pd.DataFrame(data={'bookworm': bookworm,
                                    'harmless': harmless,
                                    'shakespear': shakespear,
                                    'tl;dr': tldr})
    metrics_df.index = ['{year} {month}'.format(year=idx.year, month=calendar.month_name[idx.month])
                        for idx in metrics_df.index]
    metrics_df = metrics_df.dropna(axis=0)[:-1].iloc[::-1]
    with open(os.path.join(output, 'metrics.html'), 'w') as f:
        f.write(metrics_df.to_html(col_space=10))

    sb.set_style('darkgrid')

    # overall PR histogram
    pr_df = time_grouped_df[gitparser.AUTHOR].count()[:-1]
    ax = pr_df.plot(linewidth=2)
    ax.set_ylabel('no. pull requests')
    ax.set_title('No. merged pull requests per month')
    plt.gca().set_ylim(bottom=0)
    ax.get_figure().savefig(os.path.join(output, 'prs.png'))
    plt.close()

    # avg reviews by month
    avg_reviews_df = time_grouped_df[gitparser.NO_REVIEWS].mean()[:-1]
    ax = avg_reviews_df.plot(colormap='tab10', linewidth=2)
    ax.set_ylabel(gitparser.NO_REVIEWS)
    ax.set_title('Avg reviews per month')
    plt.gca().set_ylim(bottom=0)
    ax.get_figure().savefig(os.path.join(output, 'avg_reviews.png'))
    plt.close()

    # grab x labels for bar chart
    x_labels_0 = ax.get_xticklabels(0)[::-1]
    x_labels_1 = ax.get_xticklabels(1)
    for i in range(len(x_labels_1)):
        if len(x_labels_1[i].get_text()) == 0:
            x_labels_1[i] = x_labels_0.pop()

    # authors by month
    authors_df = time_author_grouped_df[gitparser.AUTHOR].size().groupby(level=0).size()[:-1]
    ax = authors_df.plot(colormap='tab10', linewidth=2, kind='bar')
    # fix labels
    ax.set_xticklabels(x_labels_1, minor=0)

    ax.set_ylabel('no. authors')
    ax.set_title('No. authors per month')
    plt.gca().set_ylim(bottom=0)
    ax.get_figure().savefig(os.path.join(output, 'authors.png'))
    plt.close()

    # reviews / author by month
    reviews_author_df = (time_grouped_df[gitparser.NO_REVIEWS].sum() / authors_df)[:-1]
    ax = reviews_author_df.plot(colormap='tab10', linewidth=2)
    ax.set_ylabel('reviews / authors')
    ax.set_title('Reviews / authors per month')
    plt.gca().set_ylim(bottom=0)
    ax.get_figure().savefig(os.path.join(output, 'reviews_by_authors.png'))
    plt.close()

    # PRs by author
    pr_author_df = prs_by_author.fillna(0.)[:-1]
    ax = pr_author_df.plot(colormap='tab10', linewidth=2)
    ax.set_ylabel('no. merged pull requests')
    ax.set_title('No. merged pull requests by author per month')
    plt.gca().set_ylim(bottom=1)
    lgd = ax.legend(loc=9, bbox_to_anchor=(1.3, 1.0))
    ax.get_figure().savefig(os.path.join(output, 'prs_by_author.png'),
                            additional_artists=[lgd], bbox_inches="tight")
    plt.close()

    # reviews by reviewer
    reviews_df = reviews_by_person.fillna(0.)[:-1]
    ax = reviews_df.plot(colormap='tab10', linewidth=2)
    ax.set_ylabel('no. reviews')
    ax.set_title('No. reviews by reviewer per month')
    plt.gca().set_ylim(bottom=1)
    lgd = ax.legend(loc=9, bbox_to_anchor=(1.3, 1.0))
    ax.get_figure().savefig(os.path.join(output, 'reviews_by_reviewer.png'),
                            additional_artists=[lgd], bbox_inches="tight")
    plt.close()
