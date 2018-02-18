""" Graphing functions """
import datetime
import logging
import os

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


def daterange_groupby(labels, ranges):
    def mapping_fn(index):
        for i, (from_dt, to_dt) in enumerate(ranges):
            if from_dt <= index < to_dt:
                return labels[i]
    return mapping_fn


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
    freq_str = view_text.lower()[:-2].replace('i', 'y')
    xticks, ranges, xticklabels = generate_xticks(start_date, frequency)
    # filter by earliest datetime in range
    df = df[df.index > ranges[0][0]]

    # groupings
    time_grouped_df = df.groupby(daterange_groupby(xticks, ranges))
    time_author_grouped_df = df.groupby([daterange_groupby(xticks, ranges), gitparser.AUTHOR])

    try:
        # PRs by author
        df_prs = pd.DataFrame(index=xticks, columns=authors, data=0)
        df_prs[authors] = time_author_grouped_df[gitparser.AUTHOR].count().unstack(fill_value=0)
        df_prs.to_json(os.path.join(output, 'prs.json'))

        fig, ax = plt.subplots(figsize=(7, 4))
        df_prs[authors[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_ylabel('no. merged pull requests')
        ax.set_title('No. merged pull requests by author per {}'.format(freq_str))
        plt.gca().set_ylim(bottom=0)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc='upper left')
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'prs.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()

        # authors by month
        df_authors = df_prs.clip(upper=1)
        df_authors.to_json(os.path.join(output, 'authors.json'))

        fig, ax = plt.subplots(figsize=(7, 4))
        df_authors[authors[::-1]].plot.bar(colormap='tab10', linewidth=2, stacked=True, ax=ax)
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_ylabel('no. authors')
        ax.set_title('No. authors per {}'.format(freq_str))
        plt.gca().set_ylim(bottom=0)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc='upper left')
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'authors.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()
    except Exception as e:
        logging.exception(e)

    try:
        # reviews by reviewer
        df_reviews = pd.DataFrame(index=xticks, columns=review_authors, data=0)
        df_reviews[review_authors] = time_grouped_df[review_authors].sum().loc[:, review_authors]
        df_reviews.to_json(os.path.join(output, 'reviews.json'))

        fig, ax = plt.subplots(figsize=(7, 4))
        df_reviews[review_authors[::-1]].plot.bar(colormap='tab10', linewidth=2, stacked=True, ax=ax)
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_ylabel('no. reviews received')
        ax.set_title('No. reviews received by reviewer per {}'.format(freq_str))
        plt.gca().set_ylim(bottom=1)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc='upper left')
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'reviews.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()

    except Exception as e:
        logging.exception(e)

    try:
        # avg reviews by month
        df_avg_reviews = pd.DataFrame(index=xticks, columns=['mean', 'std'], data=0)
        df_avg_reviews['mean'] = time_grouped_df[gitparser.NO_REVIEWS].mean()
        df_avg_reviews['std'] = time_grouped_df[gitparser.NO_REVIEWS].std()
        df_avg_reviews.to_json(os.path.join(output, 'avg_reviews.json'))

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.errorbar(x=range(len(xticks)), y=df_avg_reviews['mean'], yerr=df_avg_reviews['std'], fmt='o',
                    markersize=8, capsize=8)
        ax.set_xticklabels([], minor=1)
        ax.set_xticklabels([''] + [l for i, l in enumerate(xticklabels )if i % 2 == 0], rotation=0)
        ax.set_xlabel('date')
        ax.set_ylabel(gitparser.NO_REVIEWS)
        ax.set_title('Avg reviews per {}'.format(freq_str))
        plt.gca().set_ylim(bottom=0)
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'avg_reviews.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()
    except Exception as e:
        logging.exception(e)


def plot_commit_stats(df, output, authors, start_date, frequency='M', view_text='Monthly',
                      bgcolor='#FAFAFA', textcolor='#212121'):
    df = df[df[gitparser.AUTHOR].isin(authors)]
    freq_str = view_text.lower()[:-2].replace('i', 'y')
    xticks, ranges, xticklabels = generate_xticks(start_date, frequency)

    # groupings
    time_grouped_df = df.groupby(daterange_groupby(xticks, ranges))
    time_author_grouped_df = df.groupby([daterange_groupby(xticks, ranges), gitparser.AUTHOR])

    try:
        # commits
        df_commits = pd.DataFrame(index=xticks, columns=authors, data=0)
        df_commits[authors] = time_author_grouped_df[gitparser.TITLE].count().unstack(gitparser.AUTHOR, fill_value=0).loc[:, authors]
        df_commits.to_json(os.path.join(output, 'commits.json'))

        fig, ax = plt.subplots(figsize=(7, 4))
        df_commits[df_commits.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_ylabel('no. commits')
        ax.set_title('No. commits by author per {}'.format(freq_str))
        plt.gca().set_ylim(bottom=1)
        commit_handles, commit_labels = ax.get_legend_handles_labels()
        ax.legend(commit_handles[::-1], commit_labels[::-1], loc='upper left')
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'commits.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()
    except Exception as e:
        logging.exception(e)

    try:
        # file changes
        df_insertions = pd.DataFrame(index=xticks, columns=authors, data=0)
        df_insertions[authors] = time_author_grouped_df[gitparser.INSERTIONS].sum().unstack(
            gitparser.AUTHOR, fill_value=0).loc[:, authors]
        df_insertions.to_json(os.path.join(output, 'insertions.json'))

        df_deletions = pd.DataFrame(index=xticks, columns=authors, data=0)
        df_deletions[authors] = time_author_grouped_df[gitparser.DELETIONS].sum().unstack(
            gitparser.AUTHOR, fill_value=0).loc[:, authors]
        df_deletions.to_json(os.path.join(output, 'deletions.json'))

        fig, ax = plt.subplots(figsize=(7, 4))
        df_insertions[df_insertions.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
        ax.set_prop_cycle(None)
        (-df_deletions)[df_deletions.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
        ax.axhline(0, color='white')
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
        # code changes
        df_code = pd.DataFrame(index=xticks, columns=authors, data=0)
        df_code[authors] = time_author_grouped_df[gitparser.CODE_CHANGES].sum().unstack(
            gitparser.AUTHOR, fill_value=0).loc[:, authors]
        df_code.to_json(os.path.join(output, 'code.json'))

        fig, ax = plt.subplots(figsize=(7, 4))
        df_code[df_code.columns[::-1]].plot.bar(colormap='tab10', linewidth=2, ax=ax, stacked=True)
        ax.set_xticklabels(xticklabels, rotation=0)
        ax.set_ylabel('code lines changed')
        ax.set_title('LOC changed by author per {}'.format(freq_str))
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(power_ten_formatter))
        ax.legend(commit_handles[::-1], commit_labels[::-1], loc='upper left')
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'code.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()
    except Exception as e:
        logging.exception(e)
    try:
        # avg changes per commit by month
        df_avg_changes = pd.DataFrame(index=xticks, columns=['mean', 'std'], data=0)
        df_avg_changes['mean'] = time_grouped_df[gitparser.CODE_CHANGES].mean()
        df_avg_changes['std'] = time_grouped_df[gitparser.CODE_CHANGES].std()
        df_avg_changes.to_json(os.path.join(output, 'avg_changes.json'))

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.errorbar(x=range(len(xticks)), y=df_avg_changes['mean'],
                    yerr=df_avg_changes['std'], fmt='o',
                    markersize=8, capsize=8)
        # sb.violinplot(x=frequency, y=gitparser.CODE_CHANGES, data=df, ax=ax, color=plt.cm.tab20c(1), cut=0)
        ax.set_xticklabels([], minor=1)
        ax.set_xticklabels([''] + [l for i, l in enumerate(xticklabels) if i % 2 == 0], rotation=0)
        ax.set_ylabel(gitparser.CODE_CHANGES)
        ax.set_xlabel('date')
        # ax.set_yscale('log')
        ax.set_title('Average LOC changed per commit')
        ax.set_ylabel('code lines changed')
        plt.gca().set_ylim(bottom=0)
        set_ax_color(ax, textcolor)
        fig.savefig(os.path.join(output, 'avg_changes.png'), bbox_inches='tight', facecolor=bgcolor)
        plt.close()

    except Exception as e:
        logging.exception(e)

    # punch card
    plot = punchcard.plot_punchcard(1000, 400, df.index)
    plot.write_to_png(os.path.join(output, 'punchcard.png'))


def compute_next_datetime(dt, frequency):
    if frequency == 'M':
        next_d = datetime.datetime(dt.year, dt.month, 1) - datetime.timedelta(seconds=1)
        return next_d
    elif frequency == 'W':
        return dt - datetime.timedelta(days=7)
    elif frequency == 'D':
        return dt - datetime.timedelta(days=1)
    else:
        raise NotImplementedError('Not implemented for frequency {}'.format(frequency))


def compute_penultimate_datetime(dt, frequency):
    if frequency == 'M':
        return datetime.datetime(dt.year, dt.month, 1, 0) - datetime.timedelta(seconds=1)
    elif frequency == 'W':
        return datetime.datetime(dt.year, dt.month, dt.day - datetime.date.today().weekday(), 0) - datetime.timedelta(seconds=1)
    elif frequency == 'D':
        return datetime.datetime(dt.year, dt.month, dt.day, 0) - datetime.timedelta(seconds=1)
    else:
        raise NotImplementedError('Not implemented for frequency {}'.format(frequency))


def generate_xticks(start_date, frequency):
    ticks = []
    dt = datetime.datetime.now()
    ticks += [dt]
    dt = compute_penultimate_datetime(dt, frequency)

    while dt > start_date:
        ticks += [dt]
        dt = compute_next_datetime(dt, frequency)
    ticks += [dt]
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
