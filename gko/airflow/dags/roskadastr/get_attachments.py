import datetime
import logging
import requests
import os
import pathlib
import re
import sys
from datetime import timedelta

import exchangelib
import pendulum
from exchangelib import Account, Configuration, Credentials, EWSDateTime, EWSTimeZone


dt = sys.argv[1]
dst_dir = sys.argv[2]
server = sys.argv[3]
email = sys.argv[4]
username = sys.argv[5]
password = sys.argv[6]

def connect(server, email, username, password):
    credentials = Credentials(username=username, password=password)
    config = Configuration(server=server, credentials=credentials)
    return Account(primary_smtp_address=email, autodiscover=True, config=config, access_type=exchangelib.DELEGATE)


def get_url(text):
    url = re.search(r'"weblink_get".*?"stock".*?"count".*?"url":"(.*?)"}', text).group(1)
    token = re.search(r'"dwl_token":"(.*?)".*', text).group(1)
    name = re.search(r'"folders":.*?"list.*?"name":"(.*?)"', text).group(1)
    return {'url': f"{url}get/{token}/{name}", 'name': name}


def main(dt, dst_dir, server, email, username, password):

    account = connect(server, email, username, password)

    dt = pendulum.from_format(dt, 'YYYY-MM-DD')
    dt_next = dt + timedelta(days=1)

    try:
        path_str = account.root / 'Корневой уровень хранилища' / 'Входящие'
    except exchangelib.errors.ErrorFolderNotFound:
        raise Exception('Неверно задано имя папки!')

    emails_id = []
    tz = EWSTimeZone.localzone()

    for item in account.inbox.all().filter(
            datetime_received__range=(
                    EWSDateTime(dt.year, dt.month, dt.day, tzinfo=account.default_timezone),
                    EWSDateTime(dt_next.year, dt_next.month, dt_next.day, tzinfo=account.default_timezone)
            )
    ):
        emails_id.append(item.message_id)

        # datetime_received = item.datetime_received + timedelta(hours=3)
        #
        # if dt.date() < datetime_received.date():
        #     continue
        # elif dt.date() > datetime_received.date():
        #     break


    logging.warning(f"Emails processing - {len(emails_id)}")
    if not pathlib.Path(dst_dir).exists():
        pathlib.Path(dst_dir).mkdir(parents=True, exist_ok=True)

    for e in emails_id:
        item = path_str.get(message_id=e)
        if item:
            body = item.body
            links = re.findall(r'"(.*cloud.mail.ru.*stock.*)"', body)

            for attach in item.attachments:
                if isinstance(attach, exchangelib.FileAttachment):
                    local_path = os.path.join(dst_dir, attach.name)
                    #if not pathlib.Path(local_path).exists():
                    with open(local_path, 'wb') as f, attach.fp as fp:
                        buffer = fp.read(1024)
                        while buffer:
                            f.write(buffer)
                            buffer = fp.read(1024)
                    logging.warning(f"Downloaded attachment file - {attach.name}")

            for link in links:
                r = requests.get(link)
                if r.status_code >= 400:
                    raise Exception(f"Exception on download from link - {link}")
                text = r.text
                url = get_url(text)
                cloud_file = requests.get(url['url'])
                local_path = os.path.join(dst_dir, url['name'])
                with open(local_path, 'wb') as f:
                    f.write(cloud_file.content)
                logging.warning(f"Downloaded cloud file - {url['name']}")




if __name__ == '__main__':
    main(
        dt=dt,
        dst_dir=dst_dir,
        server=server,
        email=email,
        username=username,
        password=password
    )