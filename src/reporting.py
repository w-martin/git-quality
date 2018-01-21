""" Module for emailing notifications"""
import os
import smtplib
from email.mime.text import MIMEText

FROM_ADDRESS = 'gitquality@somewhere.com'


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

    msg = MIMEText(content)
    msg['Subject'] = '{repo} quality stats awards for {month}'.format(repo=repo_name, month=month)
    msg['From'] = FROM_ADDRESS
    msg['To'] = email_address
    s = smtplib.SMTP('localhost')
    s.sendmail(FROM_ADDRESS, [email_address], msg.as_string())
    s.close()
