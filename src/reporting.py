""" Module for emailing notifications"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import html2text

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
