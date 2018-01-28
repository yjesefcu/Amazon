#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
import os
from django.conf import settings
from errors import FileNotExist

BASE_DIR = 'd:\\media'


def _create_path(path):
    p = os.path.join(BASE_DIR, path)
    if not os.path.exists(p):
        if not os.path.exists(BASE_DIR):
            os.mkdir(BASE_DIR)
        os.mkdir(p)


def save_file(content, path, name):
    """
    保存xml文件到本地
    :param string: 文件内容
    :param path: 路径
    :param name: 文件名
    """
    _create_path(path)
    full_path = os.path.join(BASE_DIR, path)
    f = open(os.path.join(full_path, name), 'wb')
    f.write(content)
    f.close()


def get_file_content(path, name):
    """
    获取某个路径下某个文件的内容
    :param path:
    :return:
    """
    try:
        f = open(os.path.join(BASE_DIR, path, name), 'rb')
        content = ''.join(f.readlines())
    except BaseException, ex:
        raise FileNotExist('file not exist')
    return content


if __name__ == '__main__':
    save_file('asdnfsnfsd\naslkjf;sdf', 'report', '1112-122.xml')
    try:
        print get_file_content('report', '1112-122.xml')
    except FileNotExist, ex:
        print ex