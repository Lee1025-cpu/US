# -*- coding:utf-8 -*-
# @Author  : yunxu.li@united-imaging.com
# @File    : Main.py
# @Time    : 2024/10/14 10:17
# @Desc    :

# import sys

# print(__file__)
# print(sys.path)

from JsonProcess import *
from General import *


if __name__ == '__main__':
    JsonReadPath = input("请输入配置文件路径：\n")
    # JsonReadPath = "D:/code/US/GI/Label/Convert/TestData/GI_Abdomen_demo.json"

    json_data = JsonRead(JsonReadPath)
    GeneralFuncUpdate(json_data)
