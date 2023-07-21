import os
import logging
import pathlib

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)
logger.addHandler(_ch)

directory = r'D:\Мусорка\Графика\zips'

for filepath in pathlib.Path(directory).glob('**/*.mif'):
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(filepath, 'w', encoding='utf-8') as file:
        for line in lines:
            if 'Delimiter' in line:
                line = 'Delimiter ","\n'
            file.write(line)

    logger.info(filepath.name)