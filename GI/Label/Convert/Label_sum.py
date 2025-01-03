# -*- coding:utf-8 -*-
# @Author  : leiyu.chen@united-imaging.com
# @File    : Label_sum.py
# @Time    : 2024/12/04 16:45
# @Desc    :

#   步骤06：
#   1.统计txt文件中每个组织对应清晰度的数量

from collections import Counter
import copy
import numpy as np
from openpyxl import Workbook
import json
import os


def get_num(file_path, mmap):
    # 初始化一个空列表来存储文件中的每一行
    data_list = []
    # 使用with语句安全地打开文件，确保最后文件会被正确关闭
    with open(file_path, 'r', encoding='utf-8') as file:
        # 按行读取文件
        for line in file:
            # 去除每行末尾的换行符并添加到列表中
            # 使用strip()方法可以去除行首行尾的空白字符，包括换行符
            data_list.append(line.strip())

    # [A数量,B数量,C数量,没标的C数量,已标总数,该切面标记帧总数]
    d_tmp, d, map_tmp = {}, {}, {}
    for key in mmap:
        map_tmp[key] = 0

    for line in data_list:
        boxes = line.split()[2:]
        for box in boxes:
            category_id = int(box.split(',')[-2])
            d_tmp[category_id] = [0, 0, 0, 0, 0]
        # 统计某个切面标记帧总数
        for key in mmap:
            if category_id in mmap[key]:
                map_tmp[key] += 1

    for line in data_list:
        boxes = line.split()[2:]
        for box in boxes:
            category_id = int(box.split(',')[-2])
            score = int(box.split(',')[-1])
            # 总数+1
            d_tmp[category_id][-1] += 1
            if score == 0:
                d_tmp[category_id][0] += 1
            if score == 1:
                d_tmp[category_id][1] += 1
            if score == 2:
                d_tmp[category_id][2] += 1

    for key in d_tmp:
        for key_mmap in mmap:
            if key in mmap[key_mmap]:
                label_sum = map_tmp[key_mmap]

        d_tmp[key][3] = label_sum - (d_tmp[key][0]+d_tmp[key][1]+d_tmp[key][2])

    for i in sorted(d_tmp.keys()):
        d[i] = np.array(d_tmp[i])

    return d, map_tmp


def get_total(dir_1, dir_2, sum_1, sum_2):
    dir_total = copy.deepcopy(dir_1)
    for key in dir_2:
        dir_total[key] = dir_2[key] + dir_total[key]

    sum_total = copy.deepcopy(sum_1)
    for key in sum_2:
        sum_total[key] = sum_2[key] + sum_total[key]

    return dir_total, sum_total


def gen_xlsx(d, save=''):
    wb = Workbook()
    ws = wb.active
    ws.append(["ID", "A", "B", "C", "C(None)", "Total"])  # 添加表头
    for key in d:
        ws.append([key, d[key][0], d[key][1], d[key][2], d[key][3], d[key][4]])

    wb.save(save)


def get_map(map_path):
    new_map = {}

    with open(map_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    for category in data:
        new_map[category] = []
        for item in data[category]:
            new_map[category].append(data[category][item])

    return new_map


def gen_xlsx2(td, vd, save_path='train_val标记数量比值统计.xlsx'):
    wb = Workbook()
    ws = wb.active
    ws.append(["ID", "A_t:A_val", "B_t:B_val", "C_t:C_val"])  # 添加表头
    for key in td:
        # if key ==20 or key ==21 or key ==22:
        #     continue
        ws.append([key, "{}:{}".format(td[key][0], vd[key][0]), "{}:{}".format(td[key][1], vd[key][1]), "{}:{}".format(td[key][2], vd[key][2])])

    wb.save(save_path)


if __name__ == '__main__':
    # file_path_train = 'D:\\code\\ZTmp\\TrainInfo.txt'
    # file_path_val = 'D:\\code\\ZTmp\\ValInfo.txt'
    # save = 'D:\\code\\ZTmp\\'
    
    file_path_train = 'D:/code/US/GI/Label/Convert/Else/NewTrainInfo_DelSpa.txt'
    file_path_val = 'D:/code/US/GI/Label/Convert/Else/NewValInfo_DelSpa.txt'
    save = 'D:\\code\\ZTmp\\'
    mmap = get_map('D:\\code\\US\\GI\\Label\\Convert\\InputJson\\GImap.json')

    if not os.path.exists(save):
        os.makedirs(save)

    counted_numbers_train, train_sum = get_num(file_path_train, mmap)
    counted_numbers_val, val_sum = get_num(file_path_val, mmap)
    counted_numbers_total, total_sum = get_total(
        counted_numbers_train, counted_numbers_val, train_sum, val_sum)
    for key in total_sum:
        print(key, total_sum[key])
    gen_xlsx(counted_numbers_total, save=save+'标记数量统计.xlsx')
    gen_xlsx(counted_numbers_train, save=save+'train标记数量统计.xlsx')
    gen_xlsx(counted_numbers_val, save=save+'val标记数量统计.xlsx')
    gen_xlsx2(counted_numbers_train, counted_numbers_val,
              save_path=save+'train_val标记数量统计.xlsx')
