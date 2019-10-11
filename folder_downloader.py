#!/usr/bin/env python
import ctypes
import json
import os
import signal
import subprocess
import fire
from getlinkFshare import get_link_info

libc = ctypes.CDLL("libc.so.6")

FSHARE_PATH = '/root/GetLinkFshare/getlinkFshare.py'


def set_pdeathsig(sig=signal.SIGTERM):
    def call_able():
        return libc.prctl(1, sig)
    return call_able


def download(link):
    cmd = [FSHARE_PATH, 'download', link]
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = ''
    p = subprocess.Popen(cmd, shell=False, preexec_fn=set_pdeathsig(signal.SIGTERM), env=env)
    result = p.wait()
    return result


def sync_rclone(file_name, onedrive_path):
    cmd = ['rclone', 'copyto', file_name, os.path.join(onedrive_path, file_name)]
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = ''
    p = subprocess.Popen(cmd, shell=False, preexec_fn=set_pdeathsig(signal.SIGTERM), env=env)
    result = p.wait()
    return result


def download_and_sync(link_file, onedrive_path):
    with open(link_file, 'r') as fp:
        folder_link = json.load(fp)

    current_idx = json.load(open('current_idx', 'r')) if os.path.exists('current_idx') else {'current_idx': -1}
    idx = current_idx['current_idx']

    for i in range(idx + 1, len(folder_link)):
        name = folder_link[i]['name']
        link = folder_link[i]['link']
        print('Downloading: ' + name)
        r = download(link)
        if r != 0:
            break
        print("Start sync")
        r = sync_rclone(name, onedrive_path)
        if r != 0:
            break
        os.remove(name)
        current_idx = {'current_idx': idx + 1}
        with open('current_idx', 'w') as current:
            json.dump(current_idx, current)
        idx = idx + 1


def das_from_linkfile(link_file, onedrive_path):
    with open(link_file, 'r') as f:
        folder_link = f.readlines()

    current_idx = json.load(open('current_idx', 'r')) if os.path.exists('current_idx') else {'current_idx': -1}
    idx = current_idx['current_idx']

    for i in range(idx + 1, len(folder_link)):
        name = get_link_info(folder_link[i].strip())['name']
        link = folder_link[i]
        print('Downloading: ' + name)
        r = download(link)
        if r != 0:
            break
        print("Start sync")
        r = sync_rclone(name, onedrive_path)
        if r != 0:
            break
        os.remove(name)
        current_idx = {'current_idx': idx + 1}
        with open('current_idx', 'w') as current:
            json.dump(current_idx, current)
        idx = idx + 1


if __name__ == '__main__':
    fire.Fire()
