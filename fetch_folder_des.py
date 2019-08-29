#!/usr/bin/env python
import json
import os
import fire

from fshare import Fshare

with open(os.path.join(os.path.dirname(__file__), 'acc_info.json'), 'r') as fp:
    # global acc_info
    acc_info = json.load(fp=fp)

fshare = Fshare(email=acc_info['email'], password=acc_info['pass'])


def fetch_folder(folder_link, file_name, path=None):
    list_link = fshare.get_folder_info(folder_link)
    result = []
    s = 0
    for item in list_link:
        name = item['name']
        link = "https://www.fshare.vn/file/" + item['linkcode']
        size = item['size']
        s = s + size / 1024 / 1024
        result.append({'name': name, 'link': link, 'size': size})

    name_path = file_name
    if path is not None:
        name_path = os.path.join(path, file_name)
    with open(name_path, 'w') as folder_fp:
        json.dump(result, folder_fp)

    print("Total size: %f" % s)


if __name__ == '__main__':
    fire.Fire()
