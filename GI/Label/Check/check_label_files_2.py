### 检测nrrd中标签，在评分A或B的时候有没有标签

import nrrd
import os
import json
import numpy as np
import pandas as pd
import openpyxl
from tqdm import tqdm


def get_map(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def get_quality(segName_dir, path, d):
    df = pd.read_excel(path)

    for segName in segName_dir:
        li = []
        frame_arr = df.iloc[:, 1].values.astype(np.int64)
        quality_arr = df[segName].values.astype(np.int64) # 评价数组
        for i in range(frame_arr.shape[0]):
            li.append([int(frame_arr[i]), int(quality_arr[i])])

        d[segName] = li
    return d


def get_nrrd(nrrd_arr, nrrd_info, dir_tmp, nrrd_name, overlap):
    score_map = {
        0: "A",
        1: "B",
        2: "C"
    }


    seg_dic = {}
    for i in range(100):
        # 提取的名字
        seg_name = 'Segment{}_ID'.format(i)
        seg_channel = 'Segment{}_Layer'.format(i)
        seg_value = 'Segment{}_LabelValue'.format(i)

        try:
            name = nrrd_info[seg_name]
            channel = int(nrrd_info[seg_channel])
            value = int(nrrd_info[seg_value])

            seg_dic[name] = []
            seg_dic[name].append(channel)
            seg_dic[name].append(value)
        except:
            break
    
    err_info = []
    if overlap:
        if len(nrrd_arr.shape) != 4:
            err_info.append([nrrd_name.split('.dcm')[0], '警告! 标注无重叠部分, 请确认!'])

    for segName in dir_tmp:
        segInfo = dir_tmp[segName]
        for item in segInfo:
            frames_xlsx = item[0] - 1
            score_xlsx = item[1]
            if segName in seg_dic.keys():
                channel_nrrd = seg_dic[segName][0]
            else:
                continue
            # try:
            #     channel_nrrd = seg_dic[segName][0]
            # except:
            #     return False
            value_nrrd = seg_dic[segName][1]
            
            # 如果xlsx为A或B，但nrrd对应没有标签
            if score_xlsx == 0 or score_xlsx == 1:
                if len(nrrd_arr.shape) == 4:
                    slice_arr = nrrd_arr[channel_nrrd, :, :, frames_xlsx]
                else:
                    slice_arr = nrrd_arr[:, :, frames_xlsx]
                if (slice_arr == value_nrrd).any():
                    continue
                else:
                    err_info.append([nrrd_name.split('.dcm')[0], '{} 标签在 {} 帧评级为 {} 但无mask'.format(segName, frames_xlsx, score_map[score_xlsx])])
            if score_xlsx == -1:
                err_info.append([nrrd_name.split('.dcm')[0], '{} 标签在 {} 帧评级为 {} '.format(segName, frames_xlsx, score_xlsx)])



    return err_info




category_dir = {
    # true表示有重叠 false表示不重叠
    
    "PV-LS_2D_V1.0": True,
    # "PT-TS_2D_V1.0": True,
    # # "LK-LA_2D_V1.0": False,
    # # "RK-LA_2D_V1.0": False,
    # # "LK-SA_2D_V1.0": False,
    # # "RK-SA_2D_V1.0": False,
    "BL-LS_2D_V1.0": True,
    
    # "PH-TS_2D_V1.0": True,# 存在问题
    # # "BL-TS_2D_V1.0": False,
    # # "SP-LA_2D_V1.0": False,
    # # "PB-TS_2D_V1.0": False,
    # # "PH-LS_2D_V1.0": False,
}

# PB-TS_2D_V1.0//
# SP-LA_2D_V1.0
# BL-TS_2D_V1.0
# PH-LS_2D_V1.0

for category in category_dir:
    Err_info = []
    # 读json文件，获取组织seg到模型类别num的映射
    segName_dir = get_map('D:/code/US/GI/Label/Convert/InputJson/GImap.json')[category]

    overlap = category_dir[category]  # 是否应当重叠

    file_path = '//isi-wh/US/05_SW/LabelData/ImageAnalysisAnnotation/GI/{}/03_second_review_data/'.format(category)
    # file_path = '//isi-wh/US/05_SW/LabelData/ImageAnalysisAnnotation/GI/{}/04_completed_data/'.format(category)
    
    # 04_completed_data
    files = os.listdir(file_path)
    for file in tqdm(files):
        # print(file)
        
        dir_tmp = {}  # 临时字典，存seg的帧数与评分
        label_files = os.listdir(file_path+file)
        for label_file in label_files:
            if label_file[-4:] == 'xlsx' and label_file[0] != '~':
                get_quality(segName_dir, file_path+file+'/'+label_file, dir_tmp)
        
        for label_file in label_files:
            if label_file[-4:] == 'nrrd':
                
                mask, _ = nrrd.read(file_path+file+'/'+label_file)
                with open(file_path+file+'/'+label_file, 'r', encoding='utf-8', errors='ignore') as DataRead:
                    mask_info = nrrd.read_header(DataRead)
                    
                err = get_nrrd(mask, mask_info, dir_tmp, label_file, overlap)
                if err:
                    Err_info.extend(err)


    workbook = openpyxl.Workbook()
    # 获取默认的工作表
    sheet = workbook.active
    for i in range(len(Err_info)):
        name = Err_info[i][0]
        err_value = Err_info[i][1]
        sheet.append([name, err_value])
    # 保存工作簿
    workbook.save('./Result2_True/{}_Error_Save.xlsx'.format(category))



