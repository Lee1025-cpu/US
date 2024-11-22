import time
import json
import numpy as np
import os
from tqdm import tqdm


def WriteListToTxt(listtosav, saving_path, mode="w"):
    with open(saving_path, mode, encoding="utf-8") as f:
        for i in range(len(listtosav)):
            f.write(str(listtosav[i]))
            f.write("\n")

    f.close()
    

def MakeJsonandTxt(FilePath, TrainNames, ValNames, TestNames):
    # 检查3个Names是不是都在FilePath下
    Names = TrainNames + ValNames + TestNames
    for Name in Names:
        if Name not in os.listdir(FilePath):
            raise Exception(Name + " is not included in " + FilePath + ".")
    # 分别生成train, val, test的json
    # 参考 https://mmdetection.readthedocs.io/zh-cn/latest/user_guides/train.html#id8
    TrainDict, ValDict, TestDict = {}, {}, {}
    
    for Name in tqdm(TrainNames):
        filePath = FilePath + "/" + Name + "/" + Name + ".json"
        if not os.path.exists(filePath):
            raise Exception(filePath + " does not exist.")
        TrainDict[Name] = json.load(open(filePath, 'r', encoding='utf-8'))
    for Name in tqdm(ValNames):
        filePath = FilePath + "/" + Name + "/" + Name + ".json"
        if not os.path.exists(filePath):
            raise Exception(filePath + " does not exist.")
        ValDict[Name] = json.load(open(filePath, 'r', encoding='utf-8'))
    for Name in tqdm(TestNames):
        filePath = FilePath + "/" + Name + "/" + Name + ".json"
        if not os.path.exists(filePath):
            raise Exception(filePath + " does not exist.")
        TestDict[Name] = json.load(open(filePath, 'r', encoding='utf-8'))
    # 生成最终json
    with open(FilePath + "/TrainInfowithSF.json", 'w', encoding='utf-8') as f:
        f.write(json.dumps(TrainDict, indent=4, ensure_ascii=False, default=default_dump))
    f.close()
    with open(FilePath + "/ValInfowithSF.json", 'w', encoding='utf-8') as f:
        f.write(json.dumps(ValDict, indent=4, ensure_ascii=False, default=default_dump))
    f.close()
    with open(FilePath + "/TestInfowithSF.json", 'w', encoding='utf-8') as f:
        f.write(json.dumps(TestDict, indent=4, ensure_ascii=False, default=default_dump))
    f.close()       
    # 生成最终txt
    TrainTxt, ValTxt, TestTxt = [], [], []
    for key in tqdm(TrainDict.keys()):
        for i in range(len(TrainDict[key]['annotations'])):
            index = TrainDict[key]['annotations'][i]['slice_index']
            info = key + '__' + str(index).zfill(8)
            TrainTxt.append(info)
    for key in tqdm(ValDict.keys()):
        for i in range(len(ValDict[key]['annotations'])):
            index = ValDict[key]['annotations'][i]['slice_index']
            info = key + '__' + str(index).zfill(8)
            ValTxt.append(info)
    for key in tqdm(TestDict.keys()):
        for i in range(len(TestDict[key]['annotations'])):
            index = TestDict[key]['annotations'][i]['slice_index']
            info = key + '__' + str(index).zfill(8)
            TestTxt.append(info)
    WriteListToTxt(TrainTxt, FilePath + "/TrainInfowithSF.txt")
    WriteListToTxt(ValTxt, FilePath + "/ValInfowithSF.txt")
    WriteListToTxt(TestTxt, FilePath + "/TestInfowithSF.txt")
    
    
def JsonRead(JsonReadPath):
    if not os.path.exists(JsonReadPath):
        raise Exception("JsonReadPath" + JsonReadPath + " does not exist.")
    
    json_data = json.load(open(JsonReadPath, 'r', encoding='utf-8'))
    
    if 'LogPath' not in json_data.keys():
        raise Exception("LogPath is not included in Json.")
            
    if not os.path.exists(json_data['LogPath']):
        os.makedirs(json_data['LogPath'])

    KeyNeed = ['Scene', 'NeedReTrans', 'MarkMapping', 'Information']
    InformationKeyNeed = ['Name', 'FilePath', 'Keypoint', 'Segmentation']
    AllNames = []
    with open(json_data['LogPath'] + "/" + "AnnaConvertLog.txt", 'a', encoding='utf-8') as f:
        t = time.localtime()
        TimeInfo = str(t.tm_year) + "-" + str(t.tm_mon) + "-" + str(t.tm_mday) + " " + str(t.tm_hour) + ":" + str(t.tm_min) + ":" + str(t.tm_sec)
        f.write("**"*30 + "\n")
        f.write(TimeInfo + ", JsonReadPath is " + JsonReadPath + "\n")

        # 需要check key是否全面
        for key in KeyNeed:
            if key not in json_data.keys():
                raise Exception("Key " + key + " is not included in Json.")
        
        # check其他
        if len(json_data['Information']) == 0:
            raise Exception("Information does not exist.")
        
        for i in range(len(json_data['Information'])):
            for key in InformationKeyNeed:
                if key not in json_data['Information'][i].keys():
                    raise Exception("Key " + key + " is not included in " + json_data['Information'][i]['Name'] + ".")
                
            if len(json_data['Information'][i]['FilePath']) == 0:
                raise Exception(json_data['Information'][i]['Name'] + " FilePath does not exist.")
            else:
                for file in json_data['Information'][i]['FilePath']:
                    if not os.path.exists(file):
                        raise Exception(json_data['Information'][i]['Name'] + " FilePath File " + file + " does not exist.")
    
            if len(json_data['Information'][i]['Keypoint']) == 0 and len(json_data['Information'][i]['Segmentation']) == 0:
                raise Exception(json_data['Information'][i]['Name'] + " Keypoint and Segmentation does not exist.")
            AllNames.append(json_data['Information'][i]['Name'])
            
    if 'StartFrame' in json_data.keys():
        if isinstance(json_data['StartFrame'], str):
            if not os.path.exists(json_data['StartFrame']):
                raise Exception("StartFrame File doesn't exist.")
            else:
                StartFrame = json.load(open(json_data['StartFrame'], 'r', encoding='utf-8'))
                json_data['StartFrame'] = StartFrame
                
        if isinstance(json_data['StartFrame'], dict):
            if len(json_data['StartFrame'].keys()) == 0:
                raise Exception("StartFrame Dict is empty.")

    bJudgeinStartFrame, bJudgeinAllNames = False, False
    json_data['NeedReTransFrom'] = 'None'
    if len(json_data['NeedReTrans']) > 0:
        for item in json_data['NeedReTrans']:
            if 'StartFrame' in json_data.keys() and (item not in json_data['StartFrame'].keys()) and (item not in AllNames):
                raise Exception("NeedReTrans " + item + " is not included in StartFrame nor Allnames.")
            if item in json_data['StartFrame'].keys():
                bJudgeinStartFrame = True
                json_data['NeedReTransFrom'] = 'StartFrame'
            if item in AllNames:
                bJudgeinAllNames = True
                json_data['NeedReTransFrom'] = 'AllNames'
                
        if bJudgeinStartFrame and bJudgeinAllNames:
            raise Exception("NeedReTrans " + item + " is included in StartFrame and Allnames.")
            
    f.close()
    return json_data


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
        f.write(json.dumps(JsonData, indent=4,
                ensure_ascii=False, default=default_dump))
