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
import datetime


def ReadTxtToList(txt_path):
    """
        将txt_path中的内容以list形式返回
        :param txt_path:
        :return:
    """
    container = []
    if not os.path.exists(txt_path):
        raise Exception(txt_path, " does not exist")
    
    with open(txt_path, "r", encoding="utf-8") as f:
        containers = f.readlines()
        for item in containers:
            container.append(item[:-1])

    f.close()
    return container


def FindFileName(FilePath):
    ErrMsg = ""
    bHasDcm = False
    for file in os.listdir(FilePath):
        # if file.endswith('.dcm') and FilePath.strip('/').split('.')[-1] == file.split('.')[-2]: # 后半部分逻辑判断是为了处理一个文件夹下两个dcm的情况
        if file.endswith('.dcm'):
            DcmPath = FilePath + file
            bHasDcm = True
    if not bHasDcm:
        ErrMsg = "未找到dcm文件"
    
    CriteriaExcelPath = '.dcm.xlsx'
    LabelNrrdPath = '.nrrd'
    PointNrrdPath = '.nrrd'
    CandidateNrrdPath = []
    
    # 0：没有nrrd文件，2：有两个nrrd文件；3：只有一个nrrd文件，且为point文件；4：只有一个nrrd文件，且为label文件；5：只有一个nrrd文件，且为label和point文件
    OnlyOneNrrd = 0
    
    for file in os.listdir(FilePath):
        if file.endswith('.xlsx') and "~" not in file:
            CriteriaExcelPath = FilePath + file
        if file.endswith('.nrrd'):
            CandidateNrrdPath.append(FilePath + file)

    if len(CandidateNrrdPath) == 1:
        # 当只存在一个nrrd文件时，默认为label文件
        if "point" in CandidateNrrdPath[0]:
            LabelNrrdPath = ''
            PointNrrdPath = CandidateNrrdPath[0]
            OnlyOneNrrd = 3
        elif "seg" in CandidateNrrdPath[0]:
            LabelNrrdPath = CandidateNrrdPath[0]
            PointNrrdPath = ''
            OnlyOneNrrd = 4
        else:
            LabelNrrdPath = CandidateNrrdPath[0]
            PointNrrdPath = CandidateNrrdPath[0]
            OnlyOneNrrd = 5
            
    elif len(CandidateNrrdPath) == 2:
        OnlyOneNrrd = 2
        for file in CandidateNrrdPath:
            if "label" in file:
                LabelNrrdPath = file
            if "point" in file:
                PointNrrdPath = file
    else:
        ErrMsg += " Nrrd文件数量不正确"
                                    
    return DcmPath, CriteriaExcelPath, LabelNrrdPath, PointNrrdPath, OnlyOneNrrd, ErrMsg



def GetSliceNum(DcmPath):
    ErrMsg = ""
    AllSliceNum = 0
    if os.path.exists(DcmPath):
        # starttime = datetime.datetime.now()
        DcmImg = pydicom.dcmread(DcmPath, stop_before_pixels=True)
        # endtime = datetime.datetime.now()
        # print("Dcm " + str((endtime - starttime).microseconds / 1000), " ms")
        
        # TODO AttributeError: 'FileDataset' object has no attribute 'StopTrim' 是因爲多了一個dcm 保存錯誤，需要刪除
        AllSliceNum = int(DcmImg.StopTrim) - int(DcmImg.StartTrim) + 1
        # if AllSliceNum < 100:
        #     ErrMsg = "Dicom SliceNum < 100"
    else:
        ErrMsg = "No such DcmPath"
    return AllSliceNum, ErrMsg


def ReadPointData(Points, PointNrrdPath):
    ErrMsg = ""
    if os.path.exists(PointNrrdPath):
        starttime = datetime.datetime.now()
        Pointdata, _ = nrrd.read(PointNrrdPath)
        with open(PointNrrdPath, 'r', encoding='utf-8', errors='ignore') as PointRead:
            Pointheader = nrrd.read_header(PointRead)
        endtime = datetime.datetime.now()
        # print("Pointdata " + str((endtime - starttime).microseconds / 1000), " ms")
        
        Width, Height, Slice = Pointdata.shape
        PointNames, PointLayers, PointValues = [], {}, {}
        for SegIdx in range(100):
            if 'Segment' + str(SegIdx) + '_Name' in Pointheader.keys():
                PointName = Pointheader['Segment' + str(SegIdx) + '_Name']
                if PointName not in Points:
                    ErrMsg = " PointName " + PointName + " is not in the json file."
                    # continue
                
                PointNames.append(PointName)
                PointLayers[PointName] = int(Pointheader['Segment' + str(SegIdx) + '_Layer'])
                PointValues[PointName] = int(Pointheader['Segment' + str(SegIdx) + '_LabelValue'])
        return Pointdata, Width, Height, Slice, PointNames, PointLayers, PointValues, ErrMsg
    else:
        ErrMsg = "No PointNrrdPath, please check"
        return 0, 0, 0, 0, 0, 0, 0, ErrMsg


def Read3DLabelData(Segmentations, Labeldata, Labelheader):
    ErrMsg = ""
        
    Width, Height, Slice = Labeldata.shape
    LabelNames, LabelLayers, LabelValues = [], {}, {}
    for SegIdx in range(100):
        if 'Segment' + str(SegIdx) + '_Name' in Labelheader.keys():
            LabelName = Labelheader['Segment' + str(SegIdx) + '_Name']
            if LabelName not in Segmentations:
                ErrMsg = " LabelName " + LabelName + " is not in the json file."
                # continue
            
            LabelNames.append(LabelName)
            LabelLayers[LabelName] = int(Labelheader['Segment' + str(SegIdx) + '_Layer'])
            LabelValues[LabelName] = int(Labelheader['Segment' + str(SegIdx) + '_LabelValue'])
            
    return Labeldata, Width, Height, Slice, LabelNames, LabelLayers, LabelValues, ErrMsg


def Read4DLabelData(Segmentations, Data, DataHeader):
    ErrMsg = ""

    Channel, Width, Height, Slice = Data.shape

    Labeldata = np.zeros((Channel, Width, Height, Slice))
    
    LabelNames, LabelLayers, LabelValues = [], {}, {}
    for SegIdx in range(100):
        if 'Segment' + str(SegIdx) + '_Name' in DataHeader.keys():
            LabelName = DataHeader['Segment' + str(SegIdx) + '_Name']    
            if LabelName not in Segmentations:
                ErrMsg = " LabelName " + LabelName + " is not in the json file."
                # continue
            
            LabelNames.append(LabelName)
            LabelLayers[LabelName] = int(DataHeader['Segment' + str(SegIdx) + '_Layer'])
            LabelValues[LabelName] = int(DataHeader['Segment' + str(SegIdx) + '_LabelValue'])
            X, Y, Z = np.where(Data[LabelLayers[LabelName], :, :, :] == LabelValues[LabelName])
            Labeldata[LabelLayers[LabelName], X, Y, Z] = LabelValues[LabelName]

    return Labeldata, Width, Height, Slice, LabelNames, LabelLayers, LabelValues, ErrMsg


def Read4DData2in1(Points, Segmentations, Data, DataHeader):
    ErrMsg = ""
        
    Channel, Width, Height, Slice = Data.shape
                                            
    Pointdata, Labeldata = np.zeros((Width, Height, Slice)), np.zeros((Channel, Width, Height, Slice))
    
    PointNames, PointLayers, PointValues = [], {}, {}
    LabelNames, LabelLayers, LabelValues = [], {}, {}
    for SegIdx in range(100):
        if 'Segment' + str(SegIdx) + '_Name' in DataHeader.keys():
            Name = DataHeader['Segment' + str(SegIdx) + '_Name']
            if Name in Points:
                PointNames.append(Name)
                PointLayers[Name] = int(DataHeader['Segment' + str(SegIdx) + '_Layer'])
                PointValues[Name] = int(DataHeader['Segment' + str(SegIdx) + '_LabelValue'])
                X, Y, Z = np.where(Data[PointLayers[Name], :, :, :] == PointValues[Name])
                Pointdata[X, Y, Z] = PointValues[Name]
            elif Name in Segmentations:
                LabelNames.append(Name)
                LabelLayers[Name] = int(DataHeader['Segment' + str(SegIdx) + '_Layer'])
                LabelValues[Name] = int(DataHeader['Segment' + str(SegIdx) + '_LabelValue'])
                X, Y, Z = np.where(Data[LabelLayers[Name], :, :, :] == LabelValues[Name])
                Labeldata[LabelLayers[Name], X, Y, Z] = LabelValues[Name]
            else:
                ErrMsg = " " + Name + " is not in the PointName nor in MaskName."
    return Pointdata, Labeldata, Width, Height, Slice, PointNames, PointLayers, PointValues, LabelNames, LabelLayers, LabelValues, ErrMsg


def Read3DData2in1(Points, Segmentations, Data, DataHeader):
    ErrMsg = ""
    Width, Height, Slice = Data.shape
                                            
    Pointdata, Labeldata = np.zeros((Width, Height, Slice)), np.zeros((Width, Height, Slice))
    
    PointNames, PointLayers, PointValues = [], {}, {}
    LabelNames, LabelLayers, LabelValues = [], {}, {}
    for SegIdx in range(100):
        if 'Segment' + str(SegIdx) + '_Name' in DataHeader.keys():
            Name = DataHeader['Segment' + str(SegIdx) + '_Name']
            if Name in Points:
                PointNames.append(Name)
                PointLayers[Name] = int(DataHeader['Segment' + str(SegIdx) + '_Layer'])
                PointValues[Name] = int(DataHeader['Segment' + str(SegIdx) + '_LabelValue'])
                X, Y, Z = np.where(Data == PointValues[Name])
                Pointdata[X, Y, Z] = PointValues[Name]
            elif Name in Segmentations:
                LabelNames.append(Name)
                LabelLayers[Name] = int(DataHeader['Segment' + str(SegIdx) + '_Layer'])
                LabelValues[Name] = int(DataHeader['Segment' + str(SegIdx) + '_LabelValue'])
                X, Y, Z = np.where(Data == LabelValues[Name])
                Labeldata[X, Y, Z] = LabelValues[Name]
            else:
                ErrMsg = " " + Name + " is not in the PointName nor in MaskName."
    return Pointdata, Labeldata, Width, Height, Slice, PointNames, PointLayers, PointValues, LabelNames, LabelLayers, LabelValues, ErrMsg


def GeneralFunc(json_data):
    with open(json_data['LogPath'] + "/" + "AnnaConvertLog.txt", 'a', encoding='utf-8') as f:   
        with open(json_data['LogPath'] + "/" + "JsonPaths.txt", 'a', encoding='utf-8') as JsPs:
            t = time.localtime()
            TimeInfo = str(t.tm_year) + "-" + str(t.tm_mon) + "-" + str(t.tm_mday) + " " + str(t.tm_hour) + ":" + str(t.tm_min) + ":" + str(t.tm_sec)
            JsPs.write("**"*30 + "\n")
            JsPs.write(TimeInfo + "\n") 
            for InfoIdx in range(len(json_data['Information'])):
                Prob1, Prob2 = True, True
                Information = json_data['Information'][InfoIdx]
                # 只关注配置文件中设置的Target
                TarNames = list(set(Information['Keypoint']) | set(Information['Segmentation']))
                
                # 判断是否需要重传：如果NeedReTrans不为空，则判断Name是否在NeedReTrans中，只处理在NeedReTrans中的；如果NeedReTrans为空，则全部处理。
                if json_data['NeedReTransFrom'] == 'AllNames':
                    Prob1 = len(json_data['NeedReTrans'] > 0) and (Information['Name'] in json_data['NeedReTrans'])
                    Prob2 = len(json_data['NeedReTrans']) == 0
                    
                if Prob1 or Prob2:
                    SectionPath = Information['FilePath']
                    
                    for SrcPath in SectionPath:
                        for ImgIdIdx in tqdm(range(len(os.listdir(SrcPath)))):
                            FileId = os.listdir(SrcPath)[ImgIdIdx]
                            # print(FileId)
                            
                            if json_data['NeedReTransFrom'] == 'StartFrame':
                                Prob3 = FileId in json_data['NeedReTrans'] or FileId[:-4] in json_data['NeedReTrans']
                            else:
                                if 'StartFrame' in json_data.keys():
                                    Prob3 = FileId in json_data['StartFrame'] or FileId[:-4] in json_data['StartFrame']
                                else:
                                    Prob3 = True
                                    
                            # FileId like 'UIH_20240820_0820-001_20240820.094540.650_m_5' or 'UIH_20240820_0820-001_20240820.094540.650_m_5.dcm'
                            if Prob3:
                                f.write(SrcPath + FileId + '\n')

                                ImgId = FileId[:-4] if FileId.endswith('.dcm') else FileId
                                    
                                images, annotations, JsonSavingPaths = {}, [], []
                                FilePath = SrcPath + FileId + '/'
                                JsonSavingPath = FilePath + ImgId + 'withSF.json'  # 名字采用ImgId

                                # Read Path
                                if 'StartFrame' in json_data.keys():
                                    DiffSliceIdx = json_data['StartFrame'][ImgId]
                                else:
                                    DiffSliceIdx = 0
                                
                                DcmPath, CriteriaExcelPath, LabelNrrdPath, PointNrrdPath, OnlyOneNrrd, ErrMsg = FindFileName(FilePath)
                                if len(ErrMsg) > 0: 
                                    f.write(ErrMsg + '\n')
                                    continue

                                # Read Dicom
                                AllSliceNum, ErrMsg = GetSliceNum(DcmPath)
                                if len(ErrMsg) > 0: 
                                    f.write(ErrMsg + '\n')
                                    continue
                                
                                # Read Annotations
                                if OnlyOneNrrd == 2:
                                    # Read Point Data
                                    Pointdata, Width1, Height1, Slice1, PointNames, PointLayers, PointValues, ErrMsg = ReadPointData(Information['Keypoint'], PointNrrdPath)
                                    if len(ErrMsg) > 0: 
                                        f.write(ErrMsg + '\n')
                                    
                                    # Read Mask Data(4D or 3D)
                                    Data, _ = nrrd.read(LabelNrrdPath)
                                    with open(LabelNrrdPath, 'r', encoding='utf-8', errors='ignore') as LabelRead:
                                        DataHeader = nrrd.read_header(LabelRead)

                                    if len(Data.shape) == 4:
                                        Labeldata, Width2, Height2, Slice2, LabelNames, LabelLayers, LabelValues, ErrMsg = Read4DLabelData(Information['Segmentation'], Data, DataHeader)
                                    else:
                                        Labeldata, Width2, Height2, Slice2, LabelNames, LabelLayers, LabelValues, ErrMsg = Read3DLabelData(Information['Segmentation'], Data, DataHeader)
                                    if len(ErrMsg) > 0: 
                                        f.write(ErrMsg + '\n')
                                        
                                    if Width1 != Width2 or Height1 != Height2 or Slice1 != Slice2:
                                        f.write('point.noord 和 label.nrrd 尺寸不匹配\n')
                                        continue
                                    else:
                                        Width, Height, Slice = Width1, Height1, Slice1

                                elif OnlyOneNrrd == 5:
                                    # Read Point and Mask Data
                                    if os.path.exists(PointNrrdPath):
                                        Data, _ = nrrd.read(PointNrrdPath)
                                        with open(PointNrrdPath, 'r', encoding='utf-8', errors='ignore') as PonitRead:
                                            DataHeader = nrrd.read_header(PonitRead)
                                            
                                        if len(Data.shape) == 4:
                                            Pointdata, Labeldata, Width, Height, Slice, PointNames, PointLayers, PointValues, LabelNames, LabelLayers, LabelValues, ErrMsg = \
                                                Read4DData2in1(Information['Keypoint'], Information['Segmentation'], Data, DataHeader)
                                        else:
                                            Pointdata, Labeldata, Width, Height, Slice, PointNames, PointLayers, PointValues, LabelNames, LabelLayers, LabelValues, ErrMsg = \
                                                Read3DData2in1(Information['Keypoint'], Information['Segmentation'], Data, DataHeader)
                                        if len(ErrMsg) > 0: 
                                            f.write(ErrMsg + '\n')
                                            # continue # 质量评价会是Point+Seg的子集，所以读到了Point或者Seg之外的数据，也继续。
                                    else:
                                        f.write("NrrdPath不存在\n")
                                        continue
                                elif OnlyOneNrrd == 3:
                                    # Read Point, no seg
                                    Pointdata, Width, Height, Slice, PointNames, PointLayers, PointValues, ErrMsg = ReadPointData(Information['Keypoint'], PointNrrdPath)
                                    if len(ErrMsg) > 0: 
                                        f.write(ErrMsg + '\n')
                                        
                                    Labeldata, LabelNames, LabelLayers, LabelValues = np.zeros_like(Pointdata), [], {}, {}
                                    
                                elif OnlyOneNrrd == 4:
                                    # Read seg, no point
                                    Data, _ = nrrd.read(LabelNrrdPath)
                                    with open(LabelNrrdPath, 'r', encoding='utf-8', errors='ignore') as LabelRead:
                                        DataHeader = nrrd.read_header(LabelRead)

                                    if len(Data.shape) == 4:
                                        Labeldata, Width, Height, Slice, LabelNames, LabelLayers, LabelValues, ErrMsg = Read4DLabelData(Information['Segmentation'], Data, DataHeader)
                                    else:
                                        Labeldata, Width, Height, Slice, LabelNames, LabelLayers, LabelValues, ErrMsg = Read3DLabelData(Information['Segmentation'], Data, DataHeader)
                                    if len(ErrMsg) > 0: 
                                        f.write(ErrMsg + '\n')
                                    
                                    Pointdata, PointNames, PointLayers, PointValues = np.zeros_like(Labeldata), [], {}, {}
                                    
                                else:
                                    raise ValueError("OnlyOneNrrd should be 1, 3, 5 or 4, but got {}".format(OnlyOneNrrd))
                                    
                                # Read Criteria Data
                                if os.path.exists(CriteriaExcelPath):
                                    CriteriaExcel = pd.read_excel(CriteriaExcelPath)
                                else:
                                    f.write("No such CriteriaExcelPath, please check\n")
                                    continue
                                
                                images = {
                                    "file_name": ImgId,
                                    "height": Height,                           # y max 典型值 894
                                    "width": Width,                             # x max 典型值 1220
                                    "slice_num": AllSliceNum,                   # z max in Dicom 帧数
                                }
                                                            
                                Index = CriteriaExcel[CriteriaExcel.keys()[1]]  # '帧号（清晰、模糊、不可见对应A、B、C）'

                                for i in range(AllSliceNum):    # 不含评价的那些帧不纳入
                                    # TODO: 利用Matrix的Spacing信息 spacing标准化 加窗等操作
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
                                            if PointNames[PonitIdx] in TarNames:
                                                annotation["keypoints"][PointNames[PonitIdx]] = {}

                                        for MaskIdx in range(len(LabelNames)):
                                            if LabelNames[MaskIdx] in TarNames:
                                                annotation["segmentation"][LabelNames[MaskIdx]] = {}
                                        
                                        
                                        Slice = Pointdata[:, :, i - DiffSliceIdx]
                                        for PonitIdx in range(len(PointNames)):
                                            PointName = PointNames[PonitIdx]    # 默认点之间不存在重叠，Pointdata为三维数据
                                            if PointName in TarNames:
                                                _, Value = PointLayers[PointName], PointValues[PointName]
                                                annotation["keypoints"][PointName]["Loc"] = []
                                                annotation["keypoints"][PointName]["score"] = -1
                                                
                                                if np.sum(Slice == Value) != 0:
                                                    PxCenter = (np.where(Slice == Value)[0].mean(), np.where(Slice == Value)[1].mean())
                                                    annotation["keypoints"][PointName]["Loc"] = [PxCenter[0], PxCenter[1]]
                                            

                                        for count_contours in range(len(LabelNames)):
                                            LabelName = LabelNames[count_contours]  # 可能是三维数据或者四维数据
                                            if LabelName in TarNames:
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
                                                        # annotation["segmentation"][LabelName]["Loc"] = segmentation# in y, x order
                                                        annotation["segmentation"][LabelName]["Loc"].append(segmentation) # in y, x order

                                        # 将评分信息添加到annotation。
                                        # 对于GI 需要将分数映射
                                        ScoreDict = {
                                            "2": "A",
                                            "1": "B",
                                            "0": "C"
                                        }
                                        
                                        FlipRow = np.where(Index.values == i + 1 - DiffSliceIdx)[0][0]
                                        
                                        for count_contours in range(len(LabelNames)):
                                            if LabelNames[count_contours] in CriteriaExcel.keys():
                                                if CriteriaExcel[LabelNames[count_contours]][FlipRow] in [0, 1, 2]:
                                                    TheScore = json_data['MarkMapping'][str(int(CriteriaExcel[LabelNames[count_contours]][FlipRow]))]
                                                    annotation["segmentation"][LabelNames[count_contours]]["score"] = TheScore
                                                    if len(annotation["segmentation"][LabelNames[count_contours]]['Loc']) == 0 and TheScore > 0:
                                                        f.write(" Slice " + str(i + 1 - DiffSliceIdx) + " " + LabelNames[count_contours] + " 没有Mask，但是有评分 " + ScoreDict[str(TheScore)] + " \n")
                                                else:
                                                    f.write(" Slice " + str(i + 1 - DiffSliceIdx) + " " + LabelNames[count_contours] + " 质量评估分数存在问题\n")

                                        for count_points in range(len(PointNames)):
                                            if PointNames[count_points] in CriteriaExcel.keys():
                                                if CriteriaExcel[PointNames[count_points]][FlipRow] in [0, 1, 2]:
                                                    TheScore = json_data['MarkMapping'][str(int(CriteriaExcel[PointNames[count_points]][FlipRow]))]
                                                    annotation["keypoints"][PointNames[count_points]]["score"] = TheScore
                                                    if len(annotation["keypoints"][PointNames[count_points]]['Loc']) == 0 and TheScore > 0:
                                                        f.write(" Slice " + str(i + 1 - DiffSliceIdx) + " " + PointNames[count_points] + " 没有Mask，但是有评分 " + ScoreDict[str(TheScore)] + " \n")
                                                else:
                                                    f.write(" Slice " + str(i + 1 - DiffSliceIdx) + " " + PointNames[count_points] + " 质量评估分数存在问题\n")
                                                    
                                        annotations.append(annotation)

                                JsonWrite(JsonSavingPath, images, annotations)
                                JsonSavingPaths.append(JsonSavingPath)
                                JsPs.write(JsonSavingPath + "\n")
    print("Done. Please check " +
          json_data['LogPath'] + "\\" + "AnnaConvertLog.txt and \n" +  json_data['LogPath'] + "\\" + "JsonPaths.txt")

