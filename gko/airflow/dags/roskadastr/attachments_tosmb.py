import sys
import os
import errno
import pathlib
from smbclient import link, open_file, register_session, mkdir, rename, stat, symlink
import posixpath
from shutil import copyfileobj
import logging

dt = sys.argv[1]
src = sys.argv[2] # src local dir
dst = sys.argv[3] # dst share smb
server = sys.argv[4]
username = sys.argv[5]
password = sys.argv[6]


def join_path(host, path):
    return f"//{posixpath.join(host, path.lstrip('/'))}"

def smb_mkdir(host, base_dir, new_dir, uname, passwd):
    remote_dir = os.path.join(base_dir, new_dir)
    path_dst = join_path(host, remote_dir)

    try:
        mkdir(path_dst, username=uname, password=passwd)
    except OSError as err:
        if err.errno == errno.EEXIST:
            logging.warning(f"Folder exists - {path_dst}")
        else:
            raise err

    return remote_dir

def main(dt, src, dst, server, username, password):
    register_session(server, username=username, password=password)
    remote_dir = smb_mkdir(server, dst, dt, username, password)
    src_path = pathlib.Path(src)
    for g in src_path.glob('*'):
        if g.is_file():
            remote_file = os.path.join(remote_dir, g.name)
            remote_filepath = join_path(server, remote_file)
            with open(g, "rb") as f, open_file(remote_filepath, mode="wb") as g:
                copyfileobj(f, g)
        else:
            logging.warning(f"Unexpected - {str(g)}")

if __name__ == '__main__':
    main(
        dt=dt,
        src=src,
        dst=dst,
        server=server,
        username=username,
        password=password
    )
