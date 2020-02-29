#!/usr/bin/env python
import ctypes
import json
import os
import signal
import subprocess
import fire
from getlinkFshare import get_link_info
from getlinkFshare import get_link

libc = ctypes.CDLL("libc.so.6")

FSHARE_PATH = os.path.join(os.path.dirname(__file__), 'getlinkFshare.py')


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
        if r != 0:
            print("Script ended with some errors")
            break
        current_idx = {'current_idx': idx + 1}
        with open('current_idx', 'w') as current:
            json.dump(current_idx, current)
        idx = idx + 1


def stream_and_sync(link, sync_path):
    name = get_link_info(link)['name']
    print(name)
    dwn_link = get_link(link)
    flag = "http://download"
    if flag not in dwn_link:
        return -1
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = ''
    curl_cmd = ['curl', '-s', dwn_link]
    rclone_cmd = ['rclone', 'rcat', '--stats-one-line', '-P', '--stats', '2s', os.path.join(sync_path, name)]
    process_curl = subprocess.Popen(curl_cmd, shell=False, preexec_fn=set_pdeathsig(signal.SIGTERM), env=env, stdout=subprocess.PIPE)
    process_rclone = subprocess.Popen(rclone_cmd, shell=False, preexec_fn=set_pdeathsig(signal.SIGTERM), env=env, stdin=process_curl.stdout)

    process_curl.stdout.close()
    process_rclone.communicate()[0]
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
        print("Start streaming and sync " + name + " With size = " + str(size) + " MB")
        r = stream_and_sync(link, onedrive_path + folder_link[i]['path'])
        if r != 0:
            print("Script ended with some errors")
            break
        current_idx = {'current_idx': idx + 1}
        with open('current_idx', 'w') as current:
            json.dump(current_idx, current)
        idx = idx + 1

if __name__ == '__main__':
    fire.Fire()


