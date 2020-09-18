#!/usr/bin/env python
import json
import os
import fire
import time

from fshare import Fshare

with open(os.path.join(os.path.dirname(__file__), 'acc_info.json'), 'r') as fp:
    # global acc_info
    acc_info = json.load(fp=fp)

fshare = Fshare(email=acc_info['email'], password=acc_info['pass'])


def fetch_folder_tree(folder_link, password=None):
    list_link = fshare.get_folder_info(folder_link)
    result = []
    s = 0
    for item in list_link:
        if item['type'] == 1:
            name = item['name']
            link = "https://www.fshare.vn/file/" + item['linkcode']
            if password is not None:
                link = link + '|' + password
            size = item['size']
            path = item['path']
            s = s + size / 1024 / 1024
            result.append({'name': name, 'link': link, 'size': size, 'path': path})
        if item['type'] == 0:
            print("Fetching folder: " + item['name'], end='\r')
            time.sleep(1)
            (child_list, child_size) = fetch_folder_tree("https://www.fshare.vn/folder/" + item['linkcode'])
            result.extend(child_list)
            s = s + child_size

    return result, s

def fetch_folder(folder_link, file_name, path=None):
    password = None
    if len(folder_link.split('|')) > 1:
        password = folder_link.split('|')[1]
    (result, s) = fetch_folder_tree(folder_link.split('|')[0], password)

    name_path = file_name
    if path is not None:
        name_path = os.path.join(path, file_name)
    with open(name_path, 'w') as folder_fp:
        json.dump(result, folder_fp)

    print("\n" + "Total size: %f MB" % s)


if __name__ == '__main__':
    fire.Fire()
