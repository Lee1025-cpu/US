# -*- coding:utf-8 -*-
# @Author  : yunxu.li@united-imaging.com
# @File    : FindLostCase.py
# @Time    : 2024/12/11 09:32
# @Desc    : 

import os
import sys
sys.path.append('D:/code/')

import shutil
import numpy as np
from tqdm import tqdm
from Tools.TxtProcess import *
from Tools.ImageIO.ImageIO import *
import json


def Func():
    LostCases = ReadTxtToList("E:/TEMP/US/LostedCases.txt")
    LostCases = [item.split(" ")[0] for item in LostCases]
    LostQiemianPath = {}
    for case in LostCases:
        LostQiemianPath[case] = None

    SrcPath = "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\"
    TarQiemian = json.load(open("D:/code/US/GI/Label/Convert/InputJson/GImap.json", 'r', encoding='utf-8')).keys()
    TarFiles = ["03_second_review_data", "04_completed_data"]
    
    for Qiemian in tqdm(os.listdir(SrcPath)):
        if Qiemian in TarQiemian:
            for File in TarFiles:
                if len(os.listdir(SrcPath + Qiemian + "/" + File)) == 0:
                    continue
                for files in os.listdir(SrcPath + Qiemian + "/" + File):
                    if files in LostCases:
                        LostQiemianPath[files] = SrcPath + Qiemian + "/" + File
    with open("E:/TEMP/US/LostedCasesPath.txt", "w") as f:
        for key, value in LostQiemianPath.items():
            f.write(key + ": " + str(value) + "\n")
        
            
    # WriteDictToTxt(LostQiemianPath, "E:/TEMP/US/LostedCasesPath.txt")
                
    pass


if __name__ == '__main__':
    Func()

