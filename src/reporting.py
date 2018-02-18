""" Module for emailing notifications"""
import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import html2text
import pandas as pd

import htmls
import util


def email_awards(email_address, awards_df, repo_name, srcpath=os.getcwd()):
    """ Emails award winners to the given email address
    :param str email_address: the address to email
    :param pd.DataFrame awards_df: the awards dataframe
    """
    report_filename = os.path.join(srcpath, 'templates', 'email_report.html')
    with open(report_filename, 'r') as f:
        content = f.read()
    month = awards_df.index[0].split()[1]
    table = awards_df.to_html(col_space=5)
    content = content.format(repo=repo_name, month=month, table=table)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = '{repo} quality stats awards for {month}'.format(repo=repo_name, month=month)
    from_address = util.read_config('email')['from']
    msg['From'] = from_address
    msg['To'] = email_address
    msg.attach(MIMEText(content, 'html'))
    msg.attach(MIMEText(html2text.html2text(content), 'plain'))
    s = smtplib.SMTP('localhost')
    for e in email_address.split(','):
        s.sendmail(from_address, [e], msg.as_string())
    s.close()


def email_summary(email_address, content, subject):
    """ Emails award winners to the given email address
    :param str email_address: the address to email
    """
    from_address = util.read_config('email')['from']
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = email_address
    msg.attach(MIMEText(html2text.html2text(content), 'plain'))
    msg.attach(MIMEText(content, 'html'))
    s = smtplib.SMTP('localhost')
    for e in email_address.split(','):
        s.sendmail(from_address, [e], msg.as_string())
    s.close()


def run_tracking(pr_df, commit_df, srcpath, output, repo_name, home_url, recent_authors):
    config = util.read_config('summary')
    email = config['email']
    day = config['day']
    today = datetime.datetime.today()
    is_today = today.strftime('%A') == day
    objectives = config['objectives']
    authors = config['authors']

    monitors_str = '<tr>' \
                   '<td>{email}</td><td>{day}</td><td>{objectives}</td><td>{authors}</td>' \
                   '</tr>'.format(email=email, day=day, objectives=objectives, authors=authors)

    with open(os.path.join(srcpath, 'templates', 'tracking.html'), 'r') as f:
        tracking_text = f.read()
    target_path = os.path.join(output, 'tracking.html')
    with open(target_path, 'w') as f:
        f.write(tracking_text.format(name=repo_name,
                                     nav=htmls.compute_nav(home_url, view='', timeframe='',
                                                           recent_authors=recent_authors),
                                     home_url=home_url, timeframe='', view='',
                                     author='', monitors=monitors_str))

    if is_today:
        month_start = today - datetime.timedelta(days=14)
        week_start = today - datetime.timedelta(days=7)
        last_month_prs = pr_df[(pr_df.index >= month_start) & (pr_df.index < week_start)]
        last_week_prs = pr_df[pr_df.index >= week_start]
        last_week_commits = commit_df[commit_df.index >= week_start]
        last_mean = last_month_prs.no_reviews.mean()
        this_mean = last_week_prs.no_reviews.mean()
        review_text = 'The mean reviews per pull request was {avg_review_week:.2f}, ' \
                      '{status} previous week\'s which saw a mean rate of {avg_review_month:.2f}'.format(
            avg_review_week=this_mean, avg_review_month=last_mean,
            status='about the same as' if last_mean - 0.1 < this_mean < last_mean + 0.1 else
            'higher than' if this_mean > last_mean else 'lower than'
        )

        with open(os.path.join(srcpath, 'templates', 'summary.html'), 'r') as f:
            page_text = f.read()
        page_text = page_text.format(
            no_prs=last_week_prs.shape[0], no_commits=last_week_commits.shape[0],
            no_lines=last_week_commits.insertions.sum() + last_week_commits.deletions.sum(),
            no_code_lines=last_week_commits.code_changes.sum(),
            review_text=review_text, name=repo_name,
            link=home_url
        )
        subject = 'git-quality weekly summary'
        email_summary(email, page_text, subject)


def compute_awards(merge_df):
    # reviewed more than usual - well done
    # more changes than usual (code only) - well done
    # net deleter of the month
    # consider smaller PRs (PR changes above avg in month)
    return pd.DataFrame()
