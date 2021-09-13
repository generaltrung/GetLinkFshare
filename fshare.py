import ctypes
import json
import os
import signal
import subprocess

import requests

libc = ctypes.CDLL("libc.so.6")


def set_pdeathsig(sig=signal.SIGTERM):
    def call_able():
        return libc.prctl(1, sig)

    return call_able


def dump_token(file_path, token, session_id):
    with open(file_path, 'w') as current_token:
        data = {"token": token,
                "session_id": session_id}
        json.dump(data, current_token)


TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'token.json')
APP_INFO_PATH = os.path.join(os.path.dirname(__file__), 'app.json')

class Fshare:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        with open(APP_INFO_PATH, 'r') as fp:
            app_info = json.load(fp=fp)

        with open(TOKEN_PATH, 'r') as fp:
            token_info = json.load(fp=fp)
        self.user_agent = app_info['user_agent']
        self.app_key = app_info['app_key']
        self.token = token_info['token']
        self.session_id = token_info['session_id']
        self.isLogin = False
        self.header = {'User-Agent': self.user_agent,
                       'Content-Type': 'application/json'}

        self.login_url = "https://api.fshare.vn/api/user/login"
        self.download_url = "https://api.fshare.vn/api/session/download"
        self.refresh_url = "https://api.fshare.vn/api/user/refreshToken"

    def login(self):
        if self.isLogin is False:
            return_code = 0
            print("Login Fshare")

            data_login = {'user_email': self.email,
                          'password': self.password,
                          'app_key': self.app_key}

            response = requests.post(self.login_url, headers=self.header, data=json.dumps(data_login))
            status_code = response.status_code
            if status_code == 200:
                print("Login Successfully")
                self.isLogin = True
                result = response.json()
                self.token = result['token']
                self.session_id = result['session_id']
                dump_token(TOKEN_PATH, self.token, self.session_id)
            if status_code == 409 or status_code == 410:
                print("Account locked")
                return_code = -1

            return return_code

    def get_link(self, url, passwd=None):
        link = -1
        header = self.header
        header['Cookie'] = 'session_id=' + self.session_id

        data = {'url': url,
                'password': passwd,
                'token': self.token,
                'zipflag': 0}

        response = requests.post(self.download_url, headers=header, data=json.dumps(data))
        status_code = response.status_code
        if status_code == 200:
            result = response.json()
            link = result['location']

        return link

    def make_sure_login(self):
        if self.token != '' and self.session_id != '':
            return_code = 0
            data = {'token': self.token,
                    'app_key': self.app_key}

            response = requests.post(self.refresh_url, headers=self.header, data=json.dumps(data))
            status_code = response.status_code

            if status_code == 200:
                result = response.json()
                self.token = result['token']
                self.session_id = result['session_id']
                dump_token(TOKEN_PATH, self.token, self.session_id)

            if status_code != 200:
                self.isLogin = False
                return_code = self.login()

            return return_code
        else:
            return self.login()

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
