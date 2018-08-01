import requests
import curl
from bs4 import BeautifulSoup
import subprocess
import ctypes
import signal
import os
import json
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

    def get_link(self, url):
        data_get = {'_csrf-app': self.fs_csrf,
                    'fcode5': '',
                    'linkcode': url.split('/')[-1],
                    'withFcode5': 0}
        # self.fshare.set_option(pycurl.FOLLOWLOCATION, 0)
        download_response = self.fshare.post(self.download_url, data_get).decode()
        wait_time = int(json.loads(download_response.splitlines()[-1])['wait_time'])
        if wait_time != 0:
            self.login()
            return self.get_link(url)

        link = json.loads(download_response.splitlines()[-1])['url']
        return link

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

    def get_folder(self, url):
        link_list = self.get_folder_info(url)
        for link in link_list:
            l = self.get_link("www.fshare.vn/file/" + link['linkcode'])
            print(link['name'])
            cmd = ['wget', '--tries=0', '--restrict-file-names=nocontrol', '--continue', l]
            env = os.environ.copy()
            env['LD_LIBRARY_PATH'] = ''
            p = subprocess.Popen(cmd, shell=False, preexec_fn=set_pdeathsig(signal.SIGTERM), env=env)
            p.wait()
