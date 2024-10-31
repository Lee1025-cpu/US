import time
import json
import numpy as np
import os


def JsonRead(JsonReadPath):
    if not os.path.exists(JsonReadPath):
        raise Exception("JsonReadPath" + JsonReadPath + " does not exist.")
    
    json_data = json.load(open(JsonReadPath, 'r', encoding='utf-8'))
    
    if 'LogPath' not in json_data.keys():
        raise Exception("LogPath is not included in Json.")
    else:
        if not os.path.exists(json_data['LogPath']):
            os.path.mkdir(json_data['LogPath'])
            
    if not os.path.exists(json_data['LogPath']):
        os.path.mkdir(json_data['LogPath'])

    KeyNeed = ['Scene', 'MarkMapping', 'Information']
    InformationKeyNeed = ['Name', 'FilePath', 'Keypoint', 'Segmentation']
    with open(json_data['LogPath'] + "/" + "AnnaConvertLog.txt", 'a', encoding='utf-8') as f:
        t = time.localtime()
        TimeInfo = str(t.tm_year) + "-" + str(t.tm_mon) + "-" + str(t.tm_mday) + " " + str(t.tm_hour) + ":" + str(t.tm_min) + ":" + str(t.tm_sec)
        f.write("**"*30 + "\n")
        f.write(TimeInfo + ", JsonReadPath is " + JsonReadPath + "\n")

        # 需要check key是否全面
        for key in KeyNeed:
            if key not in json_data.keys():
                raise Exception("Key " + key + " is not included in Json.")
        for key in InformationKeyNeed:
            if key not in json_data['Information'].keys():
                raise Exception("Key " + key + " is not included in Information.")
        # check其他
        if len(json_data['Information']['FilePath']) == 0:
            raise Exception("Information FilePath does not exist.")
        else:
            for file in json_data['Information']['FilePath']:
                if not os.path.exists(file):
                    raise Exception("Information FilePath File " + file + " does not exist.")
    
    if len(json_data['Information']['Keypoint']) == 0 and len(json_data['Information']['Segmentation']) == 0:
        raise Exception("Information Keypoint or Segmentation does not exist.")
        
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
