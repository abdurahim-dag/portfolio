import sys
import os
import pathlib
import logging
import subprocess


dir = sys.argv[1] # src local dir

def unzip(file_zip, target):
    logging.warning(file_zip)
    logging.warning(target)
    subprocess.call(["7z", "x", "-w/data", file_zip, f"-o{target}"])

def iterate_folders(folder):
    for fzip in folder.glob('*.zip'):
        name = os.path.join(fzip.parent.absolute(), fzip.stem)
        os.makedirs(name, exist_ok=True)
        unzip(str(fzip.resolve()),name)

    for fzip in folder.glob('*.rar'):
        name = os.path.join(fzip.parent.absolute(), fzip.stem)
        os.makedirs(name, exist_ok=True)
        unzip(str(fzip.resolve()),name)

    for fld in folder.iterdir():
        if fld.is_dir():
            iterate_folders(fld)

def main(folder):
    dir_path = pathlib.Path(folder)
    print(dir_path)
    iterate_folders(dir_path)

if __name__ == '__main__':
    main(folder=dir)
