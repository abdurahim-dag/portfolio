import os
import logging
import pathlib

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)
logger.addHandler(_ch)

directory = r'D:\Мусорка\Графика\error\fix'

for filepath in pathlib.Path(directory).glob('**/*.mif'):
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(filepath, 'w', encoding='utf-8') as file:
        for line in lines:
            if ' CoordSys' in line:
                line = line[1:]
            file.write(line)

    logger.info(filepath.name)