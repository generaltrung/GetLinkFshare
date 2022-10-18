#!/usr/bin/env python
import ctypes
import json
import os
import signal
import subprocess
import fire
# from getlinkFshare import get_link_info
# from getlinkFshare import get_link
from fshare import Fshare
import time

libc = ctypes.CDLL("libc.so.6")

FSHARE_PATH = os.path.join(os.path.dirname(__file__), 'getlinkFshare.py')

with open(os.path.join(os.path.dirname(__file__), 'acc_info.json'), 'r') as fp:
    # global acc_info
    acc_info = json.load(fp=fp)

fshare_obj = Fshare(email=acc_info['email'], password=acc_info['pass'])


def set_pdeathsig(sig=signal.SIGTERM):
    def call_able():
        return libc.prctl(1, sig)
    return call_able


def get_link(link):
    link_paras = link.split('|')
    passwd = None
    if len(link_paras) > 1:
        passwd = link_paras[1]

    result = fshare_obj.get_link(link_paras[0], passwd)
    #print(result)
    return result


def get_link_info(url):
    return fshare_obj.get_link_info(url)


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
        r = sync_rclone(name, onedrive_path + folder_link[i]['path'])
        if r != 0:
            break
        os.remove(name)
        current_idx = {'current_idx': idx + 1}
        with open('current_idx', 'w') as current:
            json.dump(current_idx, current)
        idx = idx + 1


def das_from_linkfile(link_file, sync_path):
    with open(link_file, 'r') as f:
        folder_link = f.readlines()

    current_idx = json.load(open('current_idx', 'r')) if os.path.exists('current_idx') else {'current_idx': -1}
    idx = current_idx['current_idx']

    for i in range(idx + 1, len(folder_link)):
        link = folder_link[i].strip()
        r = stream_and_sync(link, sync_path)
        if (r != 0) and (r != 404):
            print("Script ended with some errors")
            break
        current_idx = {'current_idx': idx + 1}
        with open('current_idx', 'w') as current:
            json.dump(current_idx, current)
        idx = idx + 1


def stream_and_sync(link, sync_path):
    is_link_alive = True
    try:
        name = None
        name = get_link_info(link)['current']['name']
        print(name)
    except:
        if name is None:
            print('Error when get link info, may be link is dead')
            is_link_alive = False
        else:
            name = name.encode('utf-8').decode('latin-1')
    dwn_link = -1
    for i in range(5):
        if i > 0:
            print("Retrying: " + str(i+1) + "times")
        dwn_link = get_link(link)
        if dwn_link is not -1:
            break
        if is_link_alive:
            fshare_obj.make_sure_login()
        time.sleep(2.0)
    if dwn_link == -1:
        return 404 
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = ''
    try:
        rclone_path = os.path.join(sync_path, name)
        print(rclone_path)
    except:
        rclone_path = rclone_path.encode('utf-8').decode('latin-1') 
    print(rclone_path)
    rclone_cmd = ['rclone', 'copyurl', dwn_link, rclone_path, '-P']
    process_rclone = subprocess.Popen(rclone_cmd, shell=False, preexec_fn=set_pdeathsig(signal.SIGTERM), env=env)
    result = process_rclone.wait()
    return result


def stream_and_sync_folder(link_file, onedrive_path):
    with open(link_file, 'r') as fp:
        folder_link = json.load(fp)

    current_idx = json.load(open('current_idx', 'r')) if os.path.exists('current_idx') else {'current_idx': -1}
    idx = current_idx['current_idx']

    for i in range(idx + 1, len(folder_link)):
        name = folder_link[i]['name']
        link = folder_link[i]['link']
        size = folder_link[i]['size']/1024/1024
        try:
            print("Start streaming and sync " + name + " With size = " + str(size) + " MB")
        except:
            print("Start streaming and sync " + name.encode('utf-8').decode('latin-1') + " With size = " + str(size) + " MB")
        r = stream_and_sync(link, onedrive_path + folder_link[i]['path'])

        # Need some investigation aboud this if clause. I'll do it later
        if (r != 0) and (r != 404):
            print("Script ended with some errors")
            break
        current_idx = {'current_idx': idx + 1}
        with open('current_idx', 'w') as current:
            json.dump(current_idx, current)
        idx = idx + 1

if __name__ == '__main__':
    fire.Fire()


