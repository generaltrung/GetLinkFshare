import requests
import curl
import pycurl
from bs4 import BeautifulSoup
import subprocess
import ctypes
import signal
import os
import json
import re
libc = ctypes.CDLL("libc.so.6")


def set_pdeathsig(sig=signal.SIGTERM):
    def call_able():
        return libc.prctl(1, sig)
    return call_able


class Fshare:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.fshare = curl.Curl(base_url="https://www.fshare.vn")
        self.fshare.set_option(pycurl.COOKIEFILE, os.path.join(os.path.dirname(__file__), 'fshare.cookie'))
        self.fshare.set_option(pycurl.COOKIEJAR, os.path.join(os.path.dirname(__file__), 'fshare.cookie'))
        self.login_url = "site/login"
        self.download_url = "download/get"
        get_reponse = self.fshare.get(url=self.login_url).decode()
        self.fs_csrf = BeautifulSoup(get_reponse, 'html.parser').find("meta", attrs={'name': 'csrf-token'})\
            .get("content")
        self.isLogin = False

    def login(self):
        if self.isLogin is False:
            data_login = {'_csrf-app': self.fs_csrf,
                          'LoginForm[email]': self.email,
                          'LoginForm[password]': self.password,
                          'LoginForm[rememberMe]': 1}
            self.fshare.post(self.login_url, data_login).decode()

    def get_link(self, url, passwd=None):

        link = self.check_link(url)
        if link == -1:
            self.fshare.set_option(pycurl.FOLLOWLOCATION, 0)
            data_get_pwd = {'_csrf-app': self.fs_csrf,
                            "DownloadPasswordForm[password]": passwd}
            self.fshare.post(url, data_get_pwd)
            return re.findall(r'(Location:)(.*)', self.fshare.header())[0][1].strip()
        return link

    def make_sure_login(self):
        self.fshare.get("https://www.fshare.vn/file/manager")
        is_logged = re.findall(r'(Location:)(.*)', self.fshare.header())
        if len(is_logged) > 0:
            self.login()

    def check_link(self, url):
        self.make_sure_login()
        self.fshare.set_option(pycurl.FOLLOWLOCATION, 0)
        self.fshare.get(url)
        is_passwd = re.findall(r'(Location:)(.*)', self.fshare.header())
        if len(is_passwd) > 0:
            return is_passwd[0][1].strip()

        return -1


    def get_folder_info(self, url):
        endloop = False
        page = requests.get("https://www.fshare.vn/api/v3/files/folder?linkcode=" + url.split('/')[-1]).json()
        result = page['items']
        paging = page['_links']
        while endloop is False:
            if 'next' in paging:
                page = requests.get("https://www.fshare.vn/api/" + paging['next']).json()
                paging = page['_links']
                result.extend(page['items'])
            else:
                endloop = True
                
        return result

    def get_folder(self, url, passwd=None):
        link_list = self.get_folder_info(url)
        for link in link_list:
            l = self.get_link("https://www.fshare.vn/file/" + link['linkcode'], passwd)
            print(link['name'])
            cmd = ['wget', '--tries=0', '--restrict-file-names=nocontrol', '--continue', l]
            env = os.environ.copy()
            env['LD_LIBRARY_PATH'] = ''
            p = subprocess.Popen(cmd, shell=False, preexec_fn=set_pdeathsig(signal.SIGTERM), env=env)
            p.wait()
