import sys
import os
from exchangelib import Account, Configuration, Credentials,  Message, Mailbox
import pathlib
from smbclient import link, open_file, register_session, mkdir, rename, stat, symlink
import exchangelib
from shutil import copyfileobj
import logging


text_a = sys.argv[1]
to_a = sys.argv[2]
subject_a = sys.argv[3]
server_a = sys.argv[4]
email_a = sys.argv[5]
username_a = sys.argv[6]
password_a = sys.argv[7]


def connect(server, email, username, password):
    credentials = Credentials(username=username, password=password)
    config = Configuration(server=server, credentials=credentials)
    return Account(primary_smtp_address=email, autodiscover=True, config=config, access_type=exchangelib.DELEGATE)


def main(text, to, subject, server, email, username, password):
    account = connect(server, email, username, password)

    m = Message(
        account=account,
        subject=subject,
        body=text,
        to_recipients=[
            Mailbox(email_address=to),
        ],
    )
    m.send()

if __name__ == '__main__':
    main(
        text=text_a,
        to=to_a,
        subject=subject_a,
        email=email_a,
        server=server_a,
        username=username_a,
        password=password_a
    )
