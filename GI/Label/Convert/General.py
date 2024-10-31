# -*- coding:utf-8 -*-
# @Author  : yunxu.li@united-imaging.com
# @File    : General.py
# @Time    : 2024/10/17 14:45
# @Desc    :

import pydicom
import time
import pandas as pd
import nrrd
import numpy as np
import os
import cv2
from tqdm import tqdm
from JsonProcess import *


def FindFileName(FilePath, ImgId):
    DcmPath = FilePath + ImgId + '.dcm'
    CriteriaExcelPath = '.dcm.xlsx'
    LabelNrrdPath = '.nrrd'
    PointNrrdPath = '.nrrd'
    CandidateNrrdPath = []
    ErrMsg = ""
    OnlyOneNrrd = False
    
    for file in os.listdir(FilePath):
        if file.endswith('.xlsx') and "~" not in file:
            CriteriaExcelPath = FilePath + file
        if file.endswith('.nrrd'):
            CandidateNrrdPath.append(FilePath + file)

    if len(CandidateNrrdPath) == 1:
        LabelNrrdPath = CandidateNrrdPath[0]
        PointNrrdPath = CandidateNrrdPath[0]
        OnlyOneNrrd = True    
    elif len(CandidateNrrdPath) == 2:
        for file in CandidateNrrdPath:
            if "label" in file:
                LabelNrrdPath = file
            if "point" in file:
                PointNrrdPath = file
    else:
        ErrMsg = "Nrrd文件数量不正确"
        
    return DcmPath, CriteriaExcelPath, LabelNrrdPath, PointNrrdPath, ErrMsg, OnlyOneNrrd
    
    
def GeneralFuncUpdate(json_data):
    SectionPath = json_data['Information']['FilePath']

    with open(json_data['LogPath'] + "/" + "AnnaConvertLog.txt", 'a', encoding='utf-8') as f:
        with open(json_data['LogPath'] + "/" + "JsonPaths.txt", 'a', encoding='utf-8') as JsPs:
            t = time.localtime()
            TimeInfo = str(t.tm_year) + "-" + str(t.tm_mon) + "-" + str(t.tm_mday) + " " + str(t.tm_hour) + ":" + str(t.tm_min) + ":" + str(t.tm_sec)
            JsPs.write("**"*30 + "\n")
            JsPs.write(TimeInfo + "\n")

            for SrcPath in SectionPath:
                for ImgIdIdx in tqdm(range(len(os.listdir(SrcPath)))):
                    FileId = os.listdir(SrcPath)[ImgIdIdx]
                    if not FileId.endswith('.txt'):  # FileId like 'UIH_20240820_0820-001_20240820.094540.650_m_5' or 'UIH_20240820_0820-001_20240820.094540.650_m_5.dcm'
                        # f.write("--- " * 10 + '\n')
                        # f.write("Converting " + SrcPath + FileId + '\n')

                        ImgId = FileId[:-4] if FileId.endswith('.dcm') else FileId
                            
                        images, annotations, JsonSavingPaths = {}, [], []
                        FilePath = SrcPath + FileId + '/'
                        JsonSavingPath = FilePath + ImgId + '.json'  # 名字采用ImgId

                        # Read Path
                        if 'StartFrame' in json_data.keys() and (ImgId not in json_data['StartFrame'].keys()):
                            f.write(SrcPath + FileId + " is not in the StartFrame keys.\n")
                        if 'StartFrame' in json_data.keys() and (ImgId in json_data['StartFrame'].keys()):
                            DiffSliceIdx = json_data['StartFrame'][ImgId]
                        else:
                            DiffSliceIdx = 0
                            
                        DcmPath, CriteriaExcelPath, LabelNrrdPath, PointNrrdPath, ErrMsg, OnlyOneNrrd = FindFileName(FilePath, ImgId)
                        if len(ErrMsg) > 1:
                            f.write(SrcPath + FileId + " " + ErrMsg + '\n')

                        # Read Dicom
                        if os.path.exists(DcmPath):
                            DcmImg = pydicom.dcmread(DcmPath)
                            AllSliceNum = int(DcmImg.StopTrim) - int(DcmImg.StartTrim) + 1
                            if AllSliceNum < 100:
                                f.write(SrcPath + FileId + " Dicom SliceNum < 100\n")
                            del DcmImg
                        else:
                            f.write(SrcPath + FileId + " No such DcmPath\n")
                            continue
                        
                        if not OnlyOneNrrd:
                            # Read Point Data
                            if os.path.exists(PointNrrdPath):
                                Pointdata, _ = nrrd.read(PointNrrdPath)
                                with open(PointNrrdPath, 'r', encoding='utf-8', errors='ignore') as PointRead:
                                    Pointheader = nrrd.read_header(PointRead)
                                Width, Height, Slice = Pointdata.shape
                                PointNames, PointLayers, PointValues = [], {}, {}
                                for SegIdx in range(100):
                                    if 'Segment' + str(SegIdx) + '_Name' in Pointheader.keys():
                                        PointName = Pointheader['Segment' + str(SegIdx) + '_Name']
                                        if PointName not in json_data['Information']['Keypoint']:
                                            f.write(SrcPath + FileId + " PointName " + PointName + " is not in the json file. The current conversion has been skipped, please check the json file\n")
                                            continue
                                        
                                        PointNames.append(PointName)
                                        PointLayers[PointName] = int(Pointheader['Segment' + str(SegIdx) + '_Layer'])
                                        PointValues[PointName] = int(Pointheader['Segment' + str(SegIdx) + '_LabelValue'])
                            else:
                                f.write(SrcPath + FileId + " No PointNrrdPath, please check\n")
                                continue
                            
                            # Read Mask Data
                            if os.path.exists(LabelNrrdPath):
                                Labeldata, _ = nrrd.read(LabelNrrdPath)
                                with open(LabelNrrdPath, 'r', encoding='utf-8', errors='ignore') as LabelRead:
                                    Labelheader = nrrd.read_header(LabelRead)
                                LabelNames, LabelLayers, LabelValues = [], {}, {}
                                for SegIdx in range(100):
                                    if 'Segment' + str(SegIdx) + '_Name' in Labelheader.keys():
                                        LabelName = Labelheader['Segment' + str(SegIdx) + '_Name']
                                        if LabelName not in json_data['Information']['Segmentation']:
                                            f.write(SrcPath + FileId +  " LabelName " + LabelName + " is not in the json file. The current conversion has been skipped, please check the json file\n")
                                            continue
                                        
                                        LabelNames.append(LabelName)
                                        LabelLayers[LabelName] = int(Labelheader['Segment' + str(SegIdx) + '_Layer'])
                                        LabelValues[LabelName] = int(Labelheader['Segment' + str(SegIdx) + '_LabelValue'])
                            else:
                                f.write(SrcPath + FileId + " No labelNrrdPath, please check\n")
                                continue
                        else:
                            # Read Point and Mask Data
                            if os.path.exists(PointNrrdPath):
                                Data, _ = nrrd.read(PointNrrdPath)
                                with open(PointNrrdPath, 'r', encoding='utf-8', errors='ignore') as DataRead:
                                    DataHeader = nrrd.read_header(DataRead)
                                if len(Data.shape) == 4:
                                    Channel, Width, Height, Slice = Data.shape
                                    
                                    Pointdata, Labeldata = np.zeros((Width, Height, Slice)), np.zeros((Channel, Width, Height, Slice))
                                    
                                    PointNames, PointLayers, PointValues = [], {}, {}
                                    LabelNames, LabelLayers, LabelValues = [], {}, {}
                                    
                                    for SegIdx in range(100):
                                        if 'Segment' + str(SegIdx) + '_Name' in DataHeader.keys():
                                            Name = DataHeader['Segment' + str(SegIdx) + '_Name']
                                            if Name in json_data['Information']['Keypoint']:
                                                PointNames.append(Name)
                                                PointLayers[Name] = int(DataHeader['Segment' + str(SegIdx) + '_Layer'])
                                                PointValues[Name] = int(DataHeader['Segment' + str(SegIdx) + '_LabelValue'])
                                                X, Y, Z = np.where(Data[PointLayers[Name], :, :, :] == PointValues[Name])
                                                Pointdata[X, Y, Z] = PointValues[Name]
                                            elif Name in json_data['Information']['Segmentation']:
                                                LabelNames.append(Name)
                                                LabelLayers[Name] = int(DataHeader['Segment' + str(SegIdx) + '_Layer'])
                                                LabelValues[Name] = int(DataHeader['Segment' + str(SegIdx) + '_LabelValue'])
                                                X, Y, Z = np.where(Data[LabelLayers[Name], :, :, :] == LabelValues[Name])
                                                Labeldata[LabelLayers[Name], X, Y, Z] = LabelValues[Name]
                                            else:
                                                f.write(SrcPath + FileId + " " + Name + " is not in the PointName nor in MaskName. The current conversion has been skipped, please check the json file\n")
                                                continue
                                else:
                                    Width, Height, Slice = Data.shape
                                    
                                    Pointdata, Labeldata = np.zeros((Width, Height, Slice)), np.zeros((Width, Height, Slice))
                                    
                                    PointNames, PointLayers, PointValues = [], {}, {}
                                    LabelNames, LabelLayers, LabelValues = [], {}, {}
                                    
                                    for SegIdx in range(100):
                                        if 'Segment' + str(SegIdx) + '_Name' in DataHeader.keys():
                                            Name = DataHeader['Segment' + str(SegIdx) + '_Name']
                                            if Name in json_data['Information']['Keypoint']:
                                                PointNames.append(Name)
                                                PointLayers[Name] = int(DataHeader['Segment' + str(SegIdx) + '_Layer'])
                                                PointValues[Name] = int(DataHeader['Segment' + str(SegIdx) + '_LabelValue'])
                                                X, Y, Z = np.where(Data == PointValues[Name])
                                                Pointdata[X, Y, Z] = PointValues[Name]
                                            elif Name in json_data['Information']['Segmentation']:
                                                LabelNames.append(Name)
                                                LabelLayers[Name] = int(DataHeader['Segment' + str(SegIdx) + '_Layer'])
                                                LabelValues[Name] = int(DataHeader['Segment' + str(SegIdx) + '_LabelValue'])
                                                X, Y, Z = np.where(Data == LabelValues[Name])
                                                Labeldata[X, Y, Z] = LabelValues[Name]
                                            else:
                                                f.write(SrcPath + FileId + " " + Name + " is not in the PointName nor in MaskName. The current conversion has been skipped, please check the json file\n")
                                                continue
                            else:
                                f.write(SrcPath + FileId + " No NrrdPath, please check\n")
                                continue
                            
                        # Read Criteria Data
                        if os.path.exists(CriteriaExcelPath):
                            CriteriaExcel = pd.read_excel(CriteriaExcelPath)
                        else:
                            f.write(SrcPath + FileId + " No such CriteriaExcelPath, please check\n")
                            continue
                        
                        images = {
                            "file_name": ImgId,
                            "height": Height,                           # y max 典型值 894
                            "width": Width,                             # x max 典型值 1220
                            "slice_num": AllSliceNum,                   # z max in Dicom 帧数
                        }
                                                    
                        Index = CriteriaExcel[CriteriaExcel.keys()[1]]  # '帧号（清晰、模糊、不可见对应A、B、C）'

                        for i in range(AllSliceNum):    # 不含评价的那些帧不纳入
                            # 预处理：除了必要的强度归一化之外。切片索引。放到DataLoader里。TODO: 利用Matrix的Spacing信息 spacing标准化 加窗等操作
                            if i - DiffSliceIdx + 1 in Index.values:
                                # 场景-切面用文件夹区分 例如在GI-胰腺下
                                annotation = {
                                    # keypoints
                                    # 对那些没有标注的，keypoints给空列表
                                    # score。标注的分数。没有标注的，给-1。
                                    # 举例：{'PointName1': {"Loc": [x1, y1], "score": score1},
                                    #       'PointName2': {"Loc": [x2, y2], "score": score2}}
                                    # x y 为小数
                                    "keypoints": {},

                                    # segmentation
                                    # Mask采用polygon，都是二维坐标(x, y).
                                    # score。标注的分数。没有标注的，给-1。
                                    # 举例：{'MaskName1': {"Loc": [y11, x11, y12, x12, ...], "score": score1},
                                    #       'MaskName2': {"Loc": [y21, x21, y22, x22, ...], "score": score2}}
                                    # score 为 差或者中的 其 Loc
                                    "segmentation": {},
                                    "slice_index": i
                                }
                                for PonitIdx in range(len(PointNames)):
                                    annotation["keypoints"][PointNames[PonitIdx]] = {}

                                for MaskIdx in range(len(LabelNames)):
                                    annotation["segmentation"][LabelNames[MaskIdx]] = {}
                                
                                Slice = Pointdata[:, :, i - DiffSliceIdx]
                                for PonitIdx in range(len(PointNames)):
                                    PointName = PointNames[PonitIdx]    # 默认点之间不存在重叠，Pointdata为三维数据
                                    
                                    _, Value = PointLayers[PointName], PointValues[PointName]
                                    PxCenter = (np.where(Slice == Value)[0].mean(), np.where(Slice == Value)[1].mean())
                                    annotation["keypoints"][PointName]["Loc"] = [PxCenter[0], PxCenter[1]]
                                    annotation["keypoints"][PointName]["score"] = -1

                                for count_contours in range(0, len(LabelNames)):
                                    LabelName = LabelNames[count_contours]  # 可能是三维数据或者四维数据
                                    LabelLayer, LabelValue = LabelLayers[LabelName], LabelValues[LabelName]
                                    
                                    annotation["segmentation"][LabelName]["Loc"] = []
                                    annotation["segmentation"][LabelName]["score"] = -1
                                    if len(Labeldata.shape) == 3:  # 三维数据
                                        binary_mask = Labeldata[:, :, i - DiffSliceIdx] == LabelValue
                                    else:  # 四维数据
                                        binary_mask = Labeldata[LabelLayer, :, :, i - DiffSliceIdx] == LabelValue
                                    
                                    if np.sum(binary_mask) != 0:
                                        contours, _ = cv2.findContours(binary_mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # 根据二值图找轮廓
                                        for _, contour in enumerate(contours):
                                            # 求segmentation部分
                                            contour = np.flip(contour, axis=0)
                                            segmentation = contour.ravel().tolist()
                                            annotation["segmentation"][LabelName]["Loc"] = segmentation# in y, x order

                                # 将评分信息添加到annotation。
                                FlipRow = np.where(Index.values == i + 1 - DiffSliceIdx)[0][0]
                                for count_contours in range(len(LabelNames)):
                                    if CriteriaExcel[LabelNames[count_contours]][FlipRow] in [0, 1, 2]:
                                        TheScore = json_data['MarkMapping'][str(CriteriaExcel[LabelNames[count_contours]][FlipRow])]
                                        annotation["segmentation"][LabelNames[count_contours]]["score"] = TheScore
                                        if len(annotation["segmentation"][LabelNames[count_contours]]['Loc']) == 0 and TheScore == 2:
                                            f.write(SrcPath + FileId + " Slice " + str(i + 1 - DiffSliceIdx) + " " + LabelNames[count_contours] + " does not have Loc but has score for 2, please check \n")
                                    else:
                                        f.write(SrcPath + FileId + " Slice " + str(i + 1 - DiffSliceIdx) + " " + LabelNames[count_contours] + " 质量评估分数存在问题, please check \n")

                                annotations.append(annotation)

                        JsonWrite(JsonSavingPath, images, annotations)
                        JsonSavingPaths.append(JsonSavingPath)
                        JsPs.write(JsonSavingPath + "\n")
    print("Done. Please check " +
          json_data['LogPath'] + "\\" + "AnnaConvertLog.txt and \n" +  json_data['LogPath'] + "\\" + "JsonPaths.txt")
