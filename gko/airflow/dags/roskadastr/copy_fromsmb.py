import logging
import os
import posixpath
import sys
from shutil import copyfileobj

from smbclient import listdir, open_file, register_session, scandir


src = sys.argv[1]
dst = sys.argv[2]
server = sys.argv[3]
username = sys.argv[4]
password = sys.argv[5]


def join_path(host, path):
    return f"//{posixpath.join(host, path.lstrip('/'))}"

def iterate_folders(src, dst):
    for file_info in scandir(src):
        file_inode = file_info.inode()
        if file_info.is_file():
            dst_filepath = os.path.join(dst, file_info.name)
            with open(dst_filepath, "wb") as targetf, open_file(file_info.path, mode="rb") as srcf:
                copyfileobj(srcf, targetf)
        elif file_info.is_dir():
            if file_info.name not in ['.', '..']:
                new_dir = os.path.join(dst, file_info.name)
                os.makedirs(new_dir, exist_ok=True)
                iterate_folders(file_info.path, new_dir)
        else:
            logging.warning("Symlink: %s %d" % (file_info.name, file_inode))


def main(src, dst, server, username, password):
    register_session(server, username=username, password=password)
    path_src = join_path(server, src)
    if not os.path.exists(dst):
        os.makedirs(dst)
    for file_info in scandir(path_src):
        if file_info.is_dir():
            for target_dir in scandir(file_info.path):
                if target_dir.is_dir():
                    if not listdir(target_dir.path, '.success'):
                        dst_dir = os.path.join(dst, target_dir.name)
                        os.makedirs(dst_dir, exist_ok=True)
                        iterate_folders(target_dir.path, dst_dir)
                        open_file(os.path.join(target_dir.path, '.success'), mode="w").close()


if __name__ == '__main__':
    main(
        src=src,
        dst=dst,
        server=server,
        username=username,
        password=password
    )
