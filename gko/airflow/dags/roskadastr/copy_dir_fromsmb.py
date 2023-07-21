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
    iterate_folders(path_src, dst)



if __name__ == '__main__':
    main(
        src=src,
        dst=dst,
        server=server,
        username=username,
        password=password
    )
