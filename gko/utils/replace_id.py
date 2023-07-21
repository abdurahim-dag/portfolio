import os
import logging
import pathlib
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)
logger.addHandler(_ch)

directory = r'D:\Мусорка\Графика\zips'
i = 1

for filepath in pathlib.Path(directory).glob('**/*.mid'):
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(filepath, 'w', encoding='utf-8') as file:
        for line in lines:
            line = re.sub("^(\d+)", str(i), line)
            file.write(line)
            i += 1

    logger.info(filepath.name)