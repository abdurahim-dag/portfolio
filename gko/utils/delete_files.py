import logging
import os
import pathlib


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)
logger.addHandler(_ch)

directory_fixed = r'D:\Мусорка\Графика\error\fix'
directory_original = r'D:\Мусорка\Графика\original\zips'

fixed_files = [ p.name for p in pathlib.Path(directory_fixed).glob('*.mif')]

for filepath in pathlib.Path(directory_original).glob('*.zip'):
    name = filepath.stem.partition('.')[0] + '.mif'
    if name in fixed_files:
        os.remove(filepath.absolute())
        logger.info(f"Deleted {filepath.name}")
