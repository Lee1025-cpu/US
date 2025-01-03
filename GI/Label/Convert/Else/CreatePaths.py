# -*- coding:utf-8 -*-
# @Author  : yunxu.li@united-imaging.com
# @File    : CreatePaths.py
# @Time    : 2024/12/04 17:27
# @Desc    :
import sys
sys.path.append('D:/code/')
import json
import os
import shutil
import numpy as np
from tqdm import tqdm
from Tools.TxtProcess import *
from Tools.ImageIO.ImageIO import *

JsonPath = {
        103: "D:\\code\\US\\GI\\Label\\Convert\\InputJson\\GImap.json",
        68: "D:\\code\\US\\GI\\Label\\Convert\\InputJson\\map_v1.json"
    }

Paths = [
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\LL-AA_2D_V2.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\LL_IVC_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\PV-LS_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\RL-MT_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\FHH_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\SHH_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\PV-RP_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\GB-LA_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\GB-SA_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\L-RK_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\CBD_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\RL-MOD_2D_V1.0\\04_completed_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\PH-TS_2D_V1.0\\04_completed_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\PB-TS_2D_V1.0\\04_completed_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\PT-TS_2D_V1.0\\04_completed_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\PH-LS_2D_V1.0\\04_completed_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\Sp-LA_2D_V1.0\\04_completed_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\LK-LA_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\RK-LA_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\LK-SA_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\RK-SA_2D_V1.0\\04_completed_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\Bl-TS_2D_V1.0\\04_completed_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\Bl-LS_2D_V1.0\\04_completed_data\\"
        ]

def GetJsonPath(Path, id):
    if os.path.exists(Path + id + "/"):
        for path in os.listdir(Path + id + "/"):
            if path.endswith('withSF.json'):
                return Path + id + "/" + path
    elif os.path.exists(Path + id + ".dcm/"):
        for path in os.listdir(Path + id + ".dcm/"):
            if path.endswith('withSF.json'):
                return Path + id + ".dcm/" + path
    # raise Exception(Path + id + " No Json File")
    return False


def Func(ClassJsonPath, SavingPath, ClsNum):
    mapjson = json.load(open(ClassJsonPath, 'r', encoding='utf-8'))
    
    TrainIds = ReadTxtToList("D:\\code\\US\\GI\\Label\\Convert\\Else\\TrainIds.txt")
    ValIds = ReadTxtToList("D:\\code\\US\\GI\\Label\\Convert\\Else\\ValIds.txt")

    PointWidth = 5
    
    TrainInfo, ValInfo = [], []
    TheLostCase = []
    for path in tqdm(Paths):
        AllIds = ReadTxtToList(SavingPath + "\\AllIds\\" + path.split('\\')[-3] + "AllIds.txt")
        Qiemian = path.split('\\')[-3]
        
        for i in tqdm(range(len(AllIds))):
            if AllIds[i] == "UIH_2024102413594529_m_6_1024-005_2024102413594529_m_6.dcm_ls2s":
                i = i
                pass
            
            if AllIds[i] in ValIds or AllIds[i][:-4] in ValIds or AllIds[i] + ".dcm" in ValIds:
                JsonPath = path + AllIds[i] + "/" + AllIds[i] + "withSF.json"
                if not os.path.exists(JsonPath):
                    if not GetJsonPath(path, AllIds[i]):
                        TheLostCase.append(path + "/" + AllIds[i])
                        continue

                    JsonPath = GetJsonPath(path, AllIds[i])

                json_data = json.load(open(JsonPath, 'r', encoding='utf-8'))
                for j in range(len(json_data['annotations'])):
                    slicenum = json_data['annotations'][j]['slice_index']
                    Info = AllIds[i] + '__' + str(slicenum).zfill(8) + " " + Qiemian
                    if len(json_data['annotations'][j]['keypoints'].keys()) > 0:
                        for key in json_data['annotations'][j]['keypoints'].keys():
                            clsnm = mapjson[Qiemian][key]
                            Loc = json_data['annotations'][j]['keypoints'][key]['Loc']
                            if len(Loc) == 0:
                                continue
                            LocY, LocX = Loc[::2], Loc[1::2]
                            minY, minX, maxY, maxX = int(min(LocX)) - int(PointWidth / 2), int(min(LocY)) - int(PointWidth / 2), int(max(LocX)) + int(PointWidth / 2), int(max(LocY)) + int(PointWidth / 2)
                            
                            score = json_data['annotations'][j]['keypoints'][key]['score']
                            Info += " " + str(minX) + "," + str(minY) + "," + str(
                                maxX) + "," + str(maxY) + "," + str(clsnm) + "," + str(score)
                    if len(json_data['annotations'][j]['segmentation'].keys()) > 0:
                        for key in json_data['annotations'][j]['segmentation'].keys():
                            clsnm = mapjson[Qiemian][key]
                            Loc = json_data['annotations'][j]['segmentation'][key]['Loc']
                            if len(Loc) == 0:
                                continue
                            # 可能存在多个mask的情况
                            minX, minY, maxX, maxY = 3000, 3000, 0, 0
                            bGetMinMax = False
                            for Loc_i in range(len(Loc)):
                                if isinstance(Loc[Loc_i], int):
                                    continue
                                LocY, LocX = Loc[Loc_i][::2], Loc[Loc_i][1::2]
                                minX, minY, maxX, maxY = min(int(min(LocX)), minX), min(int(min(LocY)), minY), max(int(max(LocX)), maxX), max(int(max(LocY)), maxY)
                                bGetMinMax = True
                            if bGetMinMax:
                                score = json_data['annotations'][j]['segmentation'][key]['score']
                                Info += " " + str(minX) + "," + str(minY) + "," + str(
                                    maxX) + "," + str(maxY) + "," + str(clsnm) + "," + str(score)

                    ValInfo.append(Info)
            elif AllIds[i] in TrainIds or AllIds[i][:-4] in TrainIds or AllIds[i] + ".dcm" in TrainIds:
                JsonPath = path + AllIds[i] + "/" + AllIds[i] + "withSF.json"
                if not os.path.exists(JsonPath):
                    if not GetJsonPath(path, AllIds[i]):
                        TheLostCase.append(path + "/" + AllIds[i])
                        continue

                    JsonPath = GetJsonPath(path, AllIds[i])

                json_data = json.load(open(JsonPath, 'r', encoding='utf-8'))
                for j in range(len(json_data['annotations'])):
                    slicenum = json_data['annotations'][j]['slice_index']
                    Info = AllIds[i] + '__' + str(slicenum).zfill(8) + " " + Qiemian
                    if len(json_data['annotations'][j]['keypoints'].keys()) > 0:
                        for key in json_data['annotations'][j]['keypoints'].keys():
                            clsnm = mapjson[Qiemian][key]
                            Loc = json_data['annotations'][j]['keypoints'][key]['Loc']
                            if len(Loc) == 0:
                                continue
                            LocY, LocX = Loc[::2], Loc[1::2]
                            minY, minX, maxY, maxX = int(min(LocX)) - int(PointWidth / 2), int(min(LocY)) - int(PointWidth / 2), int(max(LocX)) + int(PointWidth / 2), int(max(LocY)) + int(PointWidth / 2)
                            score = json_data['annotations'][j]['keypoints'][key]['score']
                            Info += " " + str(minX) + "," + str(minY) + "," + str(
                                maxX) + "," + str(maxY) + "," + str(clsnm) + "," + str(score)
                    if len(json_data['annotations'][j]['segmentation'].keys()) > 0:
                        for key in json_data['annotations'][j]['segmentation'].keys():
                            clsnm = mapjson[Qiemian][key]
                            Loc = json_data['annotations'][j]['segmentation'][key]['Loc']
                            if len(Loc) == 0:
                                continue
                            # 可能存在多个mask的情况
                            minX, minY, maxX, maxY = 3000, 3000, 0, 0
                            bGetMinMax = False
                            for Loc_i in range(len(Loc)):
                                LocY, LocX = Loc[Loc_i][::2], Loc[Loc_i][1::2]
                                minX, minY, maxX, maxY = min(int(min(LocX)), minX), min(int(min(LocY)), minY), max(int(max(LocX)), maxX), max(int(max(LocY)), maxY)
                                bGetMinMax = True
                            if bGetMinMax:
                                score = json_data['annotations'][j]['segmentation'][key]['score']
                                Info += " " + str(minX) + "," + str(minY) + "," + str(
                                    maxX) + "," + str(maxY) + "," + str(clsnm) + "," + str(score)
                    TrainInfo.append(Info)
            else:
                print(AllIds[i])

    WriteListToTxt(TrainInfo, SavingPath + "TrainInfo" + str(ClsNum) + ".txt")
    WriteListToTxt(ValInfo, SavingPath + "ValInfo"+ str(ClsNum) + ".txt")
    WriteListToTxt(TheLostCase, SavingPath + "TheLostCase.txt")
    pass


def PreFunc():
    # 将肝胆的Train和val从label_train.txt和label_val.txt里面提取一下
    LGTrain, LGVal = ReadTxtToList("D:\\code\\US\\GI\\Label\\Convert\\Else\\label_train.txt"), ReadTxtToList("D:\\code\\US\\GI\\Label\\Convert\\Else\\label_val.txt")
    SavingLGTrain, SavingLGVal = [], []
    
    for line in LGTrain:
        Tar = line.split(" ")[0].split("/")[-1][:-4]
        lstindex = Tar.rfind("_")
        if Tar[:lstindex] not in SavingLGTrain:
            SavingLGTrain.append(Tar[:lstindex])    
    for line in LGVal:
        Tar = line.split(" ")[0].split("/")[-1][:-4]
        lstindex = Tar.rfind("_")
        if Tar[:lstindex] not in SavingLGVal:
            SavingLGVal.append(Tar[:lstindex])
    WriteListToTxt(SavingLGTrain, "D:\\code\\US\\GI\\Label\\Convert\\Else\\LGTrainIds.txt")
    WriteListToTxt(SavingLGVal, "D:\\code\\US\\GI\\Label\\Convert\\Else\\LGValIds.txt")
    

def Func1():
    Paths = [
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\LL-AA_2D_V2.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\LL_IVC_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\PV-LS_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\RL-MT_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\FHH_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\SHH_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\PV-RP_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\GB-LA_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\GB-SA_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\L-RK_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\CBD_2D_V1.0\\03_second_review_data\\",
        "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\RL-MOD_2D_V1.0\\04_completed_data\\"
        ]
    SavingPath = "D:\\code\\US\\GI\\Label\\Convert\\Else\\"
    for path in Paths:
        Qiemian = path.split("\\")[-3]
        TarFolders = []
        for file in os.listdir(path):
            if not file.endswith(".json") and not file.endswith(".txt"):
                TarFolders.append(file)
        WriteListToTxt(TarFolders, SavingPath + Qiemian + "AllIds.txt")
    
    
def MapFunc():
    mapjson = json.load(open(
        "D:\\code\\US\\GI\\Label\\Convert\\InputJson\\GImap.json", 'r', encoding='utf-8'))
    allcategory = []
    for Key in mapjson.keys():
        for key in mapjson[Key].keys():
            allcategory.append(Key + " " + key)
    WriteListToTxt(allcategory, "D:\\code\\US\\GI\\Label\\Convert\\Else\\AllCategory.txt")
    print(allcategory)


if __name__ == '__main__':
    # Func1()
    # PreFunc()
    # MapFunc()

    ClsNum = 68
    ClassJsonPath = JsonPath[ClsNum]
    
    SavingPath = "D:\\code\\US\\GI\\Label\\Convert\\Else\\"
    Func(ClassJsonPath, SavingPath, ClsNum)
