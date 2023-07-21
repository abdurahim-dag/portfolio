import logging
import os
import smbclient
import smbprotocol
import pandas
import re
import posixpath

def join_path(host, path):
    return f"//{posixpath.join(host, path.lstrip('/'))}"

pd = pandas.read_excel(r'D:\downloads\Информация о рынке ОН.xlsx')
screenshots_path = pd['Ссылка на скрины']
file_names = []

# \1.2 Результаты сбора и обработки информации\Запрос а Агентство по охране культурного наследия РД
source_folder = r'/ocenka/Мониторинг объектов недвижимости/2022'
target_folder = r'/ocenka/2023/ГКО2023/Проект отчета ГКО 2023_версия_3/screenshots'
server = '172.16.0.2'
username = 'atamovrb'
password = 'Ragimatamov@yandex.ru'

for path in screenshots_path:
    if path:
        m = re.match(r'.*[\\|\/](.*\.png)', str(path))
        if m and m[1]:
            file_names.append(m[1])

smbclient.register_session(server, username=username, password=password)
source = join_path(server, source_folder)
#source = '\\' + server + '\\' + source_folder

def find_dir(path):
    for d in smbclient.scandir(path, '*'):
        if d.is_dir():
            yield d.path.replace('\\', '/')
            yield from find_dir(d.path)

for d in find_dir(source):
    try:
        for file in smbclient.listdir(d, '*.png'):
            if file in file_names:
                source_file_path = os.path.join(d, file)
                target_file_path = join_path(server, os.path.join(target_folder, file))
                smbclient.copyfile(source_file_path, target_file_path)
                logging.info(f"{target_file_path}")

    except smbprotocol.exceptions.NoSuchFile:
        logging.error(f"NoSuchFiles png in {d}")
        continue
