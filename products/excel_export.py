#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
from PIL import Image
from xlwt import *

if __name__ == '__main__':
    # image = Image.open('d:\\20170603211754563000.png')
    # image.convert('RGB')
    # image.save('d:\\1.bmp')
    w = Workbook()
    ws = w.add_sheet('xlwtwas here')
    ws.write(0, 0, u'中文')

    ws.insert_bitmap('d:\\20170628205104817000.bmp', 1, 1)
    w.save('mini.xls')
