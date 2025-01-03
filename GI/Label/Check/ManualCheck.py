# -*- coding:utf-8 -*-
# @Author  : yunxu.li@united-imaging.com
# @File    : ManualCheck.py
# @Time    : 2024/11/08 10:03
# @Desc    : 

import os
import sys
sys.path.append('D:/code/')

import shutil
import numpy as np
from tqdm import tqdm
from Tools.TxtProcess import *
from Tools.ImageIO.ImageIO import *
import nrrd

def Func():
    SrcPath = "\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\PT-TS_2D_V1.0\\03_second_review_data\\UIH_20240820_0820-001_20240820.101923.758_m_16.dcm"
    PointData, _ = nrrd.read(SrcPath + '/' + SrcPath.split('\\')[-1] + '_point.nrrd')
    LabelData, _ = nrrd.read(SrcPath + '/' + SrcPath.split('\\')[-1] + '_label.nrrd')
    
    for i in tqdm(range(PointData.shape[0])):
        if PointData[i][0] == 0:
            PointData[i][0] = 1
    pass


if __name__ == '__main__':
    Func()

