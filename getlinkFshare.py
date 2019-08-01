#!/usr/bin/env python
from fshare import Fshare
from fshare import set_pdeathsig
from fshare import libc
import sys
import json
import os
import fire
import subprocess
import signal

with open(os.path.join(os.path.dirname(__file__), 'acc_info.json'), 'r') as fp:
    # global acc_info
    acc_info = json.load(fp=fp)

fshare = Fshare(email=acc_info['email'], password=acc_info['pass'])


def get_link(link):
    link_paras = link.split('|')
    passwd = None
    if len(link_paras) > 1:
        passwd = link_paras[1]
    print(fshare.get_link(link_paras[0], passwd))


def download(link):
    link_paras = link.split('|')
    passwd = None
    if len(link_paras) > 1:
        passwd = link_paras[1]
    download_link = fshare.get_link(link_paras[0], passwd)
    cmd = ['wget', '-4', '--tries=0', '--restrict-file-names=nocontrol', '--continue', download_link]
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = ''
    p = subprocess.Popen(cmd, shell=False, preexec_fn=set_pdeathsig(signal.SIGTERM), env=env)
    p.wait()


def download_folder(link):
    link_paras = link.split('|')
    passwd = None
    if len(link_paras) > 1:
        passwd = link_paras[1]
    fshare.get_folder(link_paras[0], passwd)


def download_from_file(file_name):
    with open(file_name) as link_file:
        lines = link_file.readlines()
        for link in lines:
            link_paras = link.split('|')
            passwd = None
            if len(link_paras) > 1:
                passwd = link_paras[1]
            download_link = fshare.get_link(link_paras[0].strip(), passwd)
            cmd = ['wget', '-4', '--tries=0', '--restrict-file-names=nocontrol', '--continue', download_link]
            env = os.environ.copy()
            env['LD_LIBRARY_PATH'] = ''
            p = subprocess.Popen(cmd, shell=False, preexec_fn=set_pdeathsig(signal.SIGTERM), env=env)
            p.wait()


if __name__ == '__main__':
    fire.Fire()



