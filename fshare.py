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
        self.user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0"
        self.fshare.set_option(pycurl.COOKIEFILE, os.path.join(os.path.dirname(__file__), 'fshare.cookie'))
        self.fshare.set_option(pycurl.USERAGENT, self.user_agent)
        self.login_url = "site/login"
        self.download_url = "download/get"
        get_reponse = self.fshare.get(url=self.login_url).decode()
        self.fs_csrf = BeautifulSoup(get_reponse, 'html.parser').find("meta", attrs={'name': 'csrf-token'}) \
            .get("content")
        self.isLogin = False

    def login(self):
        if self.isLogin is False:
            print("Login Fshare")
            data_login = {'_csrf-app': self.fs_csrf,
                          'LoginForm[email]': self.email,
                          'LoginForm[password]': self.password,
                          'LoginForm[rememberMe]': 1}
            self.fshare.post(self.login_url, data_login).decode()
            self.fshare.set_option(pycurl.COOKIEJAR, os.path.join(os.path.dirname(__file__), 'fshare.cookie'))

    def get_link(self, url, passwd=None):
        link = -1
        ispass = int(self.get_link_info(url)['current']['pwd'])
        if ispass == 0:
            link = self.check_link(url)
        else:
            self.fshare.set_option(pycurl.FOLLOWLOCATION, 0)
            self.fshare.get(url)
            res = re.findall(r'(Location:)(.*)', self.fshare.header())
            if len(res) > 0:
                token = "token"
                flag = "http://download"
                dwn_link = res[0][1].strip()
                if token in dwn_link:
                    self.fshare.set_option(pycurl.FOLLOWLOCATION, 0)
                    data_get_pwd = {'_csrf-app': self.fs_csrf,
                                    "DownloadPasswordForm[password]": passwd}
                    self.fshare.post(dwn_link, data_get_pwd)
                    link = re.findall(r'(Location:)(.*)', self.fshare.header())
                    if len(link) > 0:
                        if flag in link[0][1].strip():
                            return link[0][1].strip()
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
            token = "token"
            flag = "http://download"
            dwn_link = is_passwd[0][1].strip()
            if token in dwn_link:
                self.fshare.set_option(pycurl.FOLLOWLOCATION, 0)
                self.fshare.get(dwn_link)
                link = re.findall(r'(Location:)(.*)', self.fshare.header())
                if len(link) > 0:
                    if flag in link[0][1].strip():
                        return link[0][1].strip()

        return -1

    def get_link_info(self, url):
        r = requests.get("https://www.fshare.vn/api/v3/files/folder?linkcode="
                         + url.split('/')[-1].split('|')[0]).json()

        return r

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
            cmd = ['wget', '-4', '--tries=0', '--restrict-file-names=nocontrol', '--continue', l]
            env = os.environ.copy()
            env['LD_LIBRARY_PATH'] = ''
            p = subprocess.Popen(cmd, shell=False, preexec_fn=set_pdeathsig(signal.SIGTERM), env=env)
            p.wait()
