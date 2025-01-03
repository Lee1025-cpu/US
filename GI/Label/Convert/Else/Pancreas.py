# -*- coding:utf-8 -*-
# @Author  : yunxu.li@united-imaging.com
# @File    : Pancreas.py
# @Time    : 2024/10/17 14:45
# @Desc    :
import pydicom
import pandas as pd
import nrrd
import numpy as np
import os
import cv2
from tqdm import tqdm
import json
# from JsonProcess import *


SegmentationDict = {  
    2: "肠系膜上动脉", 3: "下腔静脉", 4: "脾静脉", 5: "腹主动脉", 7: "胰头", 8: "胰体", 9: "胰尾"
}

Information = {
    "MarkMapping": {
        "0": 2,
        "1": 1,
        "2": 0
    },
    "Keypoint": [],
    "Segmentation": [
        "肠系膜上动脉",
        "下腔静脉",
        "脾静脉",
        "腹主动脉",
        "胰体",
        "胰头",
        "胰尾"
    ]
}
TarNames = list(set(Information['Keypoint']) |
                set(Information['Segmentation']))


def default_dump(obj):
    """
    https://blog.csdn.net/weixin_39561473/article/details/123227500
    Convert numpy classes to JSON serializable objects.
    """
    if isinstance(obj, (np.integer, np.floating, np.bool_)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj
    
    
def JsonWrite(WrtPath, ImageList, AnnaList):
    """Json Write Func

    Args:
        WrtPath (Str): the path to write. like "E:/....../UIH_20240820_0820-001_20240820.094540.650_m_5.json"
        ImageList (List): image info in coco format
        AnnaList (List): annation info in coco format
    """
    # json write
    with open(WrtPath, 'w', encoding='utf-8') as f:
        JsonData = {}
        JsonData["images"] = ImageList
        JsonData["annotations"] = AnnaList
        f.write(json.dumps(JsonData, indent=4, ensure_ascii=False, default=default_dump))
        
        
def FindFileName(FilePath):
    ErrMsg = ""
    bHasDcm = False
    for file in os.listdir(FilePath):
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
        Pointdata, _ = nrrd.read(PointNrrdPath)
        with open(PointNrrdPath, 'r', encoding='utf-8', errors='ignore') as PointRead:
            Pointheader = nrrd.read_header(PointRead)

        Width, Height, Slice = Pointdata.shape
        PointNames, PointLayers, PointValues = [], {}, {}
        for SegIdx in range(100):
            if 'Segment' + str(SegIdx) + '_Name' in Pointheader.keys():
                PointName = Pointheader['Segment' + str(SegIdx) + '_Name']
                if PointName not in Points:
                    ErrMsg = " PointName " + PointName + " is not in the json file."
                    # continue

                PointNames.append(PointName)
                PointLayers[PointName] = int(
                    Pointheader['Segment' + str(SegIdx) + '_Layer'])
                PointValues[PointName] = int(
                    Pointheader['Segment' + str(SegIdx) + '_LabelValue'])
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
            LabelLayers[LabelName] = int(
                Labelheader['Segment' + str(SegIdx) + '_Layer'])
            LabelValues[LabelName] = int(
                Labelheader['Segment' + str(SegIdx) + '_LabelValue'])

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
            LabelLayers[LabelName] = int(
                DataHeader['Segment' + str(SegIdx) + '_Layer'])
            LabelValues[LabelName] = int(
                DataHeader['Segment' + str(SegIdx) + '_LabelValue'])
            X, Y, Z = np.where(
                Data[LabelLayers[LabelName], :, :, :] == LabelValues[LabelName])
            Labeldata[LabelLayers[LabelName], X, Y, Z] = LabelValues[LabelName]

    return Labeldata, Width, Height, Slice, LabelNames, LabelLayers, LabelValues, ErrMsg


def Read4DData2in1(Points, Segmentations, Data, DataHeader):
    ErrMsg = ""

    Channel, Width, Height, Slice = Data.shape

    Pointdata, Labeldata = np.zeros((Width, Height, Slice)), np.zeros(
        (Channel, Width, Height, Slice))

    PointNames, PointLayers, PointValues = [], {}, {}
    LabelNames, LabelLayers, LabelValues = [], {}, {}
    for SegIdx in range(100):
        if 'Segment' + str(SegIdx) + '_Name' in DataHeader.keys():
            Name = DataHeader['Segment' + str(SegIdx) + '_Name']
            if Name in Points:
                PointNames.append(Name)
                PointLayers[Name] = int(
                    DataHeader['Segment' + str(SegIdx) + '_Layer'])
                PointValues[Name] = int(
                    DataHeader['Segment' + str(SegIdx) + '_LabelValue'])
                X, Y, Z = np.where(
                    Data[PointLayers[Name], :, :, :] == PointValues[Name])
                Pointdata[X, Y, Z] = PointValues[Name]
            elif Name in Segmentations:
                LabelNames.append(Name)
                LabelLayers[Name] = int(
                    DataHeader['Segment' + str(SegIdx) + '_Layer'])
                LabelValues[Name] = int(
                    DataHeader['Segment' + str(SegIdx) + '_LabelValue'])
                X, Y, Z = np.where(
                    Data[LabelLayers[Name], :, :, :] == LabelValues[Name])
                Labeldata[LabelLayers[Name], X, Y, Z] = LabelValues[Name]
            else:
                ErrMsg = " " + Name + " is not in the PointName nor in MaskName."
    return Pointdata, Labeldata, Width, Height, Slice, PointNames, PointLayers, PointValues, LabelNames, LabelLayers, LabelValues, ErrMsg


def Read3DData2in1(Points, Segmentations, Data, DataHeader):
    ErrMsg = ""
    Width, Height, Slice = Data.shape

    Pointdata, Labeldata = np.zeros(
        (Width, Height, Slice)), np.zeros((Width, Height, Slice))

    PointNames, PointLayers, PointValues = [], {}, {}
    LabelNames, LabelLayers, LabelValues = [], {}, {}
    for SegIdx in range(100):
        if 'Segment' + str(SegIdx) + '_Name' in DataHeader.keys():
            Name = DataHeader['Segment' + str(SegIdx) + '_Name']
            if Name in Points:
                PointNames.append(Name)
                PointLayers[Name] = int(
                    DataHeader['Segment' + str(SegIdx) + '_Layer'])
                PointValues[Name] = int(
                    DataHeader['Segment' + str(SegIdx) + '_LabelValue'])
                X, Y, Z = np.where(Data == PointValues[Name])
                Pointdata[X, Y, Z] = PointValues[Name]
            elif Name in Segmentations:
                LabelNames.append(Name)
                LabelLayers[Name] = int(
                    DataHeader['Segment' + str(SegIdx) + '_Layer'])
                LabelValues[Name] = int(
                    DataHeader['Segment' + str(SegIdx) + '_LabelValue'])
                X, Y, Z = np.where(Data == LabelValues[Name])
                Labeldata[X, Y, Z] = LabelValues[Name]
            else:
                ErrMsg = " " + Name + " is not in the PointName nor in MaskName."
    return Pointdata, Labeldata, Width, Height, Slice, PointNames, PointLayers, PointValues, LabelNames, LabelLayers, LabelValues, ErrMsg


def PancreasFunc(Paths, LogSavingPath, SuccessIdsSavingPath):
    StartFramePaths = {
        'PH-TS_2D_V1.0': "D:\\code\\US\\GI\\Label\\Convert\\StartFrame\\StartFrame\\StratFrame_PH-TS_2D_V1.0.json", 
        'PB-TS_2D_V1.0': "D:\\code\\US\\GI\\Label\\Convert\\StartFrame\\StartFrame\\StratFrame_PB-TS_2D_V1.0.json",
        'PT-TS_2D_V1.0': "D:\\code\\US\\GI\\Label\\Convert\\StartFrame\\StartFrame\\StratFrame_PT-TS_2D_V1.0.json"
    }
    
    with open(LogSavingPath, 'a', encoding='utf-8') as f:   
        with open(SuccessIdsSavingPath, 'a', encoding='utf-8') as JsPs:
            for path in Paths:
                StartFrame = json.load(open(StartFramePaths[path.split("\\")[-3]], 'r', encoding='utf-8'))
                
                for FileId in tqdm(os.listdir(path)):
                    FilePath = path + FileId + '/'
                    # FileId like 'UIH_20240820_0820-001_20240820.094540.650_m_5' or 'UIH_20240820_0820-001_20240820.094540.650_m_5.dcm'
                    ImgId = FileId[:-4] if FileId.endswith('.dcm') else FileId

                    images, annotations, JsonSavingPaths = {}, [], []
                    JsonSavingPath = FilePath + ImgId + 'withSF.json'  # 名字采用ImgId
                    
                    f.write(FilePath + '\n')
                    # Read Path
                    DiffSliceIdx = StartFrame[ImgId]

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
                                    Read3DData2in1(['Keypoint'], Information['Segmentation'], Data, DataHeader)
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
                        raise ValueError(
                            "OnlyOneNrrd should be 1, 3, 5 or 4, but got {}".format(OnlyOneNrrd))

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

                    # '帧号（清晰、模糊、不可见对应A、B、C）'
                    Index = CriteriaExcel[CriteriaExcel.keys()[1]]

                    for i in range(AllSliceNum):    # 不含评价的那些帧不纳入
                        # TODO: 利用Matrix的Spacing信息 spacing标准化 加窗等操作
                        if i - DiffSliceIdx + 1 in Index.values:
                            annotation = {
                                "keypoints": {},
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

                            # 1 胰头胰体下分界点；2 胰头胰体上分界点；3 胰体胰尾下分界点；4 胰体胰尾上分界点
                            missingboundarypts = []
                            for CheckIdx in PointValues.keys():
                                if len(np.where(Slice == PointValues[CheckIdx])[0]) == 0:
                                    missingboundarypts.append(CheckIdx)
                            
                            bhasHBBoundaryPts = not (('胰头胰体下分界点' in missingboundarypts) or ('胰头胰体上分界点' in missingboundarypts))
                            bhasBTBoundaryPts = not (('胰体胰尾下分界点' in missingboundarypts) or ('胰体胰尾上分界点' in missingboundarypts))
                            
                            if len(missingboundarypts) > 0:
                                # 合理的缺失是上下分界点同时缺失
                                if len(missingboundarypts) == 1 or len(missingboundarypts) == 3 or len(missingboundarypts) == 4:
                                    f.write("错误：Slice " + str(i + 1) + ", 没有" + str(missingboundarypts) + "标注, please check\n")
                                    continue
                                if len(missingboundarypts) == 2:
                                    if not (bhasHBBoundaryPts or bhasBTBoundaryPts):
                                        f.write("错误：Slice " + str(i + 1) + ", 没有" + str(missingboundarypts) + "标注, please check\n")
                                        continue
                            
                            # label 1拆分头 体 尾
                            # 位于胰头胰体下分界点 1 和胰头胰体上分界点 2 连线左侧的部分为胰头，赋予新标签 7
                            # 位于胰体胰尾上分界点 3 和胰体胰尾下分界点 4 连线右侧的部分为胰尾，赋予新标签 8
                            # 处在label 1内 但不在上述两个区域内的为胰体，赋予新标签 9
                            if bhasHBBoundaryPts:
                                P1Center = (np.where(Slice == PointValues['胰头胰体下分界点'])[0].mean(), np.where(Slice == PointValues['胰头胰体下分界点'])[1].mean())
                                P2Center = (np.where(Slice == PointValues['胰头胰体上分界点'])[0].mean(), np.where(Slice == PointValues['胰头胰体上分界点'])[1].mean())
                                k12 = (P2Center[0] - P1Center[0]) / (P2Center[1] - P1Center[1])
                                b12 = P2Center[0] - k12 * P2Center[1]
                            if bhasBTBoundaryPts:
                                P3Center = (np.where(Slice == PointValues['胰体胰尾下分界点'])[0].mean(), np.where(Slice == PointValues['胰体胰尾下分界点'])[1].mean())
                                P4Center = (np.where(Slice == PointValues['胰体胰尾上分界点'])[0].mean(), np.where(Slice == PointValues['胰体胰尾上分界点'])[1].mean())
                                k34 = (P3Center[0] - P4Center[0]) / (P3Center[1] - P4Center[1])
                                b34 = P4Center[0] - k34 * P4Center[1]
                            
                            annotation["segmentation"]['胰头'] = {}    
                            annotation["segmentation"]['胰头']["Loc"] = []
                            annotation["segmentation"]['胰头']["score"] = -1
                            annotation["segmentation"]['胰尾'] = {}    
                            annotation["segmentation"]['胰尾']["Loc"] = []
                            annotation["segmentation"]['胰尾']["score"] = -1
                            annotation["segmentation"]['胰体'] = {}    
                            annotation["segmentation"]['胰体']["Loc"] = []
                            annotation["segmentation"]['胰体']["score"] = -1
                            annotation["segmentation"]['肠系膜上动脉'] = {}
                            annotation["segmentation"]['肠系膜上动脉']["Loc"] = []
                            annotation["segmentation"]['肠系膜上动脉']["score"] = -1
                            annotation["segmentation"]['下腔静脉'] = {}
                            annotation["segmentation"]['下腔静脉']["Loc"] = []
                            annotation["segmentation"]['下腔静脉']["score"] = -1
                            annotation["segmentation"]['脾静脉'] = {}
                            annotation["segmentation"]['脾静脉']["Loc"] = []
                            annotation["segmentation"]['脾静脉']["score"] = -1
                            annotation["segmentation"]['腹主动脉'] = {}
                            annotation["segmentation"]['腹主动脉']["Loc"] = []
                            annotation["segmentation"]['腹主动脉']["score"] = -1
                            
                            # TODO 可能是4维的数据
                            if Labeldata.ndim == 3:
                                # 将segmentation转换为coco中的格式 实质需要存的为7部分
                                # 0: background
                                # 1+6: pancreas 然后胰腺需要拆分胰头7 体8 尾9
                                # 2：SMA    肠系膜上动脉
                                # 3：IVC    下腔静脉
                                # 4：SpV    脾静脉
                                # 5：Ao     腹主动脉
                                # 6：real pancreas 不需要纳入
                                # 首先将label 6转换为1
                                label6 = np.where(Labeldata[:, :, i - DiffSliceIdx] == 6)
                                for j in range(len(label6[0])):
                                    x, y = label6[0][j], label6[1][j]
                                    Labeldata[x, y, i - DiffSliceIdx] = 1

                                label1 = np.where(Labeldata[:, :, i - DiffSliceIdx] == 1)
                                PancreasData = Labeldata[:, :, i - DiffSliceIdx]
                                
                                for j in range(len(label1[0])):
                                    x, y = label1[0][j], label1[1][j]
                                    if bhasHBBoundaryPts and y * k12 + b12 >= x:
                                        PancreasData[x, y] = 7
                                    elif bhasBTBoundaryPts and y * k34 + b34 < x:
                                        PancreasData[x, y] = 9
                                    else:
                                        PancreasData[x, y] = 8
                                        
                                for count_contours in range(2, 10):
                                    binary_mask = PancreasData[:, :] == count_contours
                                    if np.sum(binary_mask) != 0:
                                        contours, hierarchy = cv2.findContours(binary_mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  
                                        for _, contour in enumerate(contours):
                                            # 求segmentation部分
                                            contour = np.flip(contour, axis=0)
                                            segmentation = contour.ravel().tolist()
                                            if count_contours != 6:
                                                if count_contours == 4:
                                                    annotation["segmentation"][SegmentationDict[count_contours]]["Loc"].append(segmentation)
                                                    annotation["segmentation"][SegmentationDict[count_contours]]["score"] = -1
                                                else:
                                                    annotation["segmentation"][SegmentationDict[count_contours]]["Loc"].append(segmentation)
                                                    annotation["segmentation"][SegmentationDict[count_contours]]["score"] = -1
                            else:
                                # 4d数据
                                # 胰腺 layer 0， value 1 不需要的
                                # 胰体 胰头 胰尾 放2d图里 胰头7 体8 尾9
                                # 肠系膜上动脉 layer 0， value 2
                                # 下腔静脉 layer 1， value 1
                                # 脾静脉 layer 0， value 3
                                # 腹主动脉 layer 0， value 4
                                PancreasLayer, PancreasValue = LabelLayers['胰腺'], LabelValues['胰腺']
                                CXMSDMLayer, CXMSDValue = LabelLayers['肠系膜上动脉'], LabelValues['肠系膜上动脉']
                                XQJMLayer, XQJMValue = LabelLayers['下腔静脉'], LabelValues['下腔静脉']
                                PJMJLayer, PJMJValue = LabelLayers['脾静脉'], LabelValues['脾静脉']
                                FZDMLayer, FZDMValue = LabelLayers['腹主动脉'], LabelValues['腹主动脉']
                                
                                label1 = np.where(Labeldata[PancreasLayer, :, :, i - DiffSliceIdx] == PancreasValue)
                                PancreasData = np.zeros(Labeldata.shape[1: -1])
                                
                                for j in range(len(label1[0])):
                                    x, y = label1[0][j], label1[1][j]
                                    if bhasHBBoundaryPts and y * k12 + b12 >= x:
                                        PancreasData[x, y] = 7
                                    elif bhasBTBoundaryPts and y * k34 + b34 < x:
                                        PancreasData[x, y] = 9
                                    else:
                                        PancreasData[x, y] = 8
                                
                                # 分别实现
                                # 胰头7 体9 尾8
                                binary_mask = PancreasData == 7
                                if np.sum(binary_mask) != 0:
                                    contours, hierarchy = cv2.findContours(binary_mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  
                                    for _, contour in enumerate(contours):
                                        # 求segmentation部分
                                        contour = np.flip(contour, axis=0)
                                        segmentation = contour.ravel().tolist()
                                        annotation["segmentation"]['胰头']["Loc"].append(segmentation)
                                
                                binary_mask = PancreasData == 8
                                if np.sum(binary_mask) != 0:
                                    contours, hierarchy = cv2.findContours(binary_mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  
                                    for _, contour in enumerate(contours):
                                        # 求segmentation部分
                                        contour = np.flip(contour, axis=0)
                                        segmentation = contour.ravel().tolist()
                                        annotation["segmentation"]['胰体']["Loc"].append(segmentation)
                                        
                                binary_mask = PancreasData == 9
                                if np.sum(binary_mask) != 0:
                                    contours, hierarchy = cv2.findContours(binary_mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  
                                    for _, contour in enumerate(contours):
                                        # 求segmentation部分
                                        contour = np.flip(contour, axis=0)
                                        segmentation = contour.ravel().tolist()
                                        annotation["segmentation"]['胰尾']["Loc"].append(segmentation)
                                        
                                # 肠系膜上动脉
                                binary_mask = Labeldata[CXMSDMLayer, :, :, i - DiffSliceIdx] == CXMSDValue
                                if np.sum(binary_mask) != 0:
                                    contours, hierarchy = cv2.findContours(binary_mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  
                                    for _, contour in enumerate(contours):
                                        # 求segmentation部分
                                        contour = np.flip(contour, axis=0)
                                        segmentation = contour.ravel().tolist()
                                        annotation["segmentation"]['肠系膜上动脉']["Loc"].append(segmentation)
                                        
                                # 下腔静脉
                                binary_mask = Labeldata[XQJMLayer, :, :, i - DiffSliceIdx] == XQJMValue
                                if np.sum(binary_mask) != 0:
                                    contours, hierarchy = cv2.findContours(binary_mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  
                                    for _, contour in enumerate(contours):
                                        # 求segmentation部分
                                        contour = np.flip(contour, axis=0)
                                        segmentation = contour.ravel().tolist()
                                        annotation["segmentation"]['下腔静脉']["Loc"].append(segmentation)
                                        
                                # 脾静脉
                                binary_mask = Labeldata[PJMJLayer, :, :, i - DiffSliceIdx] == PJMJValue
                                if np.sum(binary_mask) != 0:
                                    contours, hierarchy = cv2.findContours(binary_mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  
                                    for _, contour in enumerate(contours):
                                        # 求segmentation部分
                                        contour = np.flip(contour, axis=0)
                                        segmentation = contour.ravel().tolist()
                                        annotation["segmentation"]['脾静脉']["Loc"].append(segmentation)
                                        
                                # 腹主动脉
                                binary_mask = Labeldata[FZDMLayer, :, :, i - DiffSliceIdx] == FZDMValue
                                if np.sum(binary_mask) != 0:
                                    contours, hierarchy = cv2.findContours(binary_mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  
                                    for _, contour in enumerate(contours):
                                        # 求segmentation部分
                                        contour = np.flip(contour, axis=0)
                                        segmentation = contour.ravel().tolist()
                                        annotation["segmentation"]['腹主动脉']["Loc"].append(segmentation)

                            # 将评分信息添加到annotation。
                            # 需要判断对应的评分是否为空。空的话，对应的score就保持-1.
                            # 首先Get帧号所在的行
                            # 对于GI 需要将分数映射
                            ScoreDict = {
                                "2": "A",
                                "1": "B",
                                "0": "C"
                            }

                            FlipRow = np.where(Index.values == i + 1 - DiffSliceIdx)[0][0]

                            for count_contours in range(len(TarNames)):
                                if TarNames[count_contours] in CriteriaExcel.keys():
                                    if CriteriaExcel[TarNames[count_contours]][FlipRow] in [0, 1, 2]:
                                        TheScore = Information['MarkMapping'][str(int(CriteriaExcel[TarNames[count_contours]][FlipRow]))]
                                        annotation["segmentation"][TarNames[count_contours]]["score"] = TheScore
                                        if len(annotation["segmentation"][TarNames[count_contours]]['Loc']) == 0 and TheScore > 0:
                                            f.write(" Slice " + str(i + 1 - DiffSliceIdx) + " " + TarNames[count_contours] + " 没有Mask，但是有评分 " + ScoreDict[str(TheScore)] + " \n")
                                    else:
                                        f.write(" Slice " + str(i + 1 - DiffSliceIdx) + " " + TarNames[count_contours] + " 质量评估分数存在问题\n")

                            annotations.append(annotation)

                    JsonWrite(JsonSavingPath, images, annotations)
                    JsonSavingPaths.append(JsonSavingPath)
                    JsPs.write(JsonSavingPath + "\n")
      
      
def PH_LSFunc(path, LogSavingPath, SuccessIdsSavingPath):
    TarNames = ['胰头']
    StartFramePaths = {
        'PH-LS_2D_V1.0': "D:\\code\\US\\GI\\Label\\Convert\\StartFrame\\StartFrame\\StratFrame_PH-LS_2D_V1.0.json"
    }
    
    with open(LogSavingPath, 'a', encoding='utf-8') as f:   
        with open(SuccessIdsSavingPath, 'a', encoding='utf-8') as JsPs:
            StartFrame = json.load(open(StartFramePaths[path.split("\\")[-3]], 'r', encoding='utf-8'))
            for FileId in tqdm(os.listdir(path)):
                FilePath = path + FileId + '/'
                # FileId like 'UIH_20240820_0820-001_20240820.094540.650_m_5' or 'UIH_20240820_0820-001_20240820.094540.650_m_5.dcm'
                ImgId = FileId[:-4] if FileId.endswith('.dcm') else FileId

                images, annotations, JsonSavingPaths = {}, [], []
                JsonSavingPath = FilePath + ImgId + 'withSF.json'  # 名字采用ImgId
                
                f.write(FilePath + '\n')
                # Read Path
                DiffSliceIdx = StartFrame[ImgId]
                # DiffSliceIdx = 0

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
                if OnlyOneNrrd == 4:
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

                else:
                    raise ValueError("OnlyOneNrrd should be 4, but got {}".format(OnlyOneNrrd))

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

                # '帧号（清晰、模糊、不可见对应A、B、C）'
                Index = CriteriaExcel[CriteriaExcel.keys()[1]]

                for i in range(AllSliceNum):    # 不含评价的那些帧不纳入
                    # TODO: 利用Matrix的Spacing信息 spacing标准化 加窗等操作
                    if i - DiffSliceIdx + 1 in Index.values:
                        annotation = {
                            "keypoints": {},
                            "segmentation": {},
                            "slice_index": i
                        }

                        for MaskIdx in range(len(LabelNames)):
                            if LabelNames[MaskIdx] in TarNames:
                                annotation["segmentation"][LabelNames[MaskIdx]] = {}

                        Slice = Labeldata[:, :, i - DiffSliceIdx]
                        
                        annotation["segmentation"]['胰头'] = {}    
                        annotation["segmentation"]['胰头']["Loc"] = []
                        annotation["segmentation"]['胰头']["score"] = -1
                        
                        # TODO 可能是4维的数据
                        if Labeldata.ndim == 3:
                            PancreasData = Labeldata[:, :, i - DiffSliceIdx]
                            binary_mask = PancreasData[:, :] == LabelValues['胰头']
                            contours, hierarchy = cv2.findContours(binary_mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)   
                            for _, contour in enumerate(contours):
                                contour = np.flip(contour, axis=0)
                                segmentation = contour.ravel().tolist()
                                annotation["segmentation"]['胰头']["Loc"].append(segmentation)
                                
                        else:
                            f.write("4D data is not supported yet\n")

                        # 将评分信息添加到annotation。
                        # 需要判断对应的评分是否为空。空的话，对应的score就保持-1.
                        # 首先Get帧号所在的行
                        # 对于GI 需要将分数映射
                        ScoreDict = {
                            "2": "A",
                            "1": "B",
                            "0": "C"
                        }

                        FlipRow = np.where(Index.values == i + 1 - DiffSliceIdx)[0][0]
                        
                        for count_contours in range(len(TarNames)):
                            if TarNames[count_contours] in CriteriaExcel.keys():
                                if CriteriaExcel[TarNames[count_contours]][FlipRow] in [0, 1, 2]:
                                    TheScore = Information['MarkMapping'][str(int(CriteriaExcel[TarNames[count_contours]][FlipRow]))]
                                    annotation["segmentation"][TarNames[count_contours]]["score"] = TheScore
                                    if len(annotation["segmentation"][TarNames[count_contours]]['Loc']) == 0 and TheScore > 0:
                                        f.write(" Slice " + str(i + 1 - DiffSliceIdx) + " " + TarNames[count_contours] + " 没有Mask，但是有评分 " + ScoreDict[str(TheScore)] + " \n")
                                else:
                                    f.write(" Slice " + str(i + 1 - DiffSliceIdx) + " " + TarNames[count_contours] + " 质量评估分数存在问题\n")

                        annotations.append(annotation)

                JsonWrite(JsonSavingPath, images, annotations)
                JsonSavingPaths.append(JsonSavingPath)
                JsPs.write(JsonSavingPath + "\n")
                

def Func():
    # # 胰头横切面 PH-TS 胰体横切面 PB-TS 胰尾横切面 PT-TS
    # SectionPath = [
    #     # '\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\PH-TS_2D_V1.0\\04_completed_data\\',
    #     # '\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\PB-TS_2D_V1.0\\04_completed_data\\',
    #     '\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\PT-TS_2D_V1.0\\04_completed_data\\',
    # ]
    # LogSavingPath = 'E:\\Data\\US\\GI\\Temp\\PancreaticSpleenKidneyBladder\\PancreaticLogs.txt'
    # SuccessIdsSavingPath = 'E:\\Data\\US\\GI\\Temp\\PancreaticSpleenKidneyBladder\\PancreaticSuccessIds.txt'
    
    # PancreasFunc(SectionPath, LogSavingPath, SuccessIdsSavingPath)
    
    # 胰头纵切面 PH-LS
    PH_LS_Path = '\\\\isi-wh\\US\\05_SW\\LabelData\\ImageAnalysisAnnotation\\GI\\PH-LS_2D_V1.0\\04_completed_data\\'
    PH_LS_LogSavingPath = 'E:\\Data\\US\\GI\\Temp\\PancreaticSpleenKidneyBladder\\PH_LSLogs.txt'
    PH_LS_SuccessIdsSavingPath = 'E:\\Data\\US\\GI\\Temp\\PancreaticSpleenKidneyBladder\\PH_LSSuccessIds.txt'
    PH_LSFunc(PH_LS_Path, PH_LS_LogSavingPath, PH_LS_SuccessIdsSavingPath)
    
    pass


if __name__ == '__main__':
    Func()
