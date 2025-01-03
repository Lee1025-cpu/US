# 基于train.txt与val.txt生成标签展示，以便检查标签位置与清晰度评分

import numpy as np
from openpyxl import Workbook
import json
import os
from tqdm import tqdm
from PIL import Image, ImageDraw, ImageFont
from pydicom.pixels import pixel_array
import cv2


color_map = {0:'lime', 1:'yellow', 2:'red'}
qxd_map = {0:'A', 1:'B', 2:'C'}


def get_IdMap(map_path):
    new_map = {}
    with open(map_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    for category in data:
        new_map[category] = []
        for item in data[category]:
            new_map[category].append(data[category][item])
    return new_map


def get_NameMap(map_path):
    new_map = {}
    with open(map_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    for category in data:
        for key in data[category]:
            new_map[data[category][key]] = key
    return new_map


def read_data2Image(image_path, SliceNum):
    if image_path[-3:] == 'png' or image_path[-3:] == 'jpg':
        img = Image.open(image_path)
    elif image_path[-3:] == 'npz':
        data = np.load(image_path)
        data = data['arr_0']
        img = Image.fromarray(data)
    elif image_path[-3:] == "dcm":
        data = pixel_array(image_path, index=SliceNum)
        img = Image.fromarray(data)
        # flag, frame = cv2.imencode(".bmp", data)
    else:
        print('{}格式不支持'.format(image_path[-3:]))

    if img.mode == 'L':
        # 将灰度图像转换为RGB图像
        img = img.convert('RGB')
    return img


def draw_1(image_path, SliceNum, box_info, name_map, save):
    """显示所有标签，并拼接原图

    Args:
        image_path (_type_): 图像路径
        box_info (_type_): box信息
        name_map (_type_): 调用get_NameMap获取
        save (_type_): 储存路径
    """
    img = read_data2Image(image_path, SliceNum)
    # 创建一个可以在给定图像上绘图的对象
    draw = ImageDraw.Draw(img)

    for box in box_info:
        # 矩形框的坐标点列表
        new_box = []
        if isinstance(box, str):
            for item in box.split(','):
                new_box.append(int(item))
        elif isinstance(box, np.ndarray):
            new_box = [item for item in box] 
        elif isinstance(box, list):
            new_box = [item for item in box] 
        else:
            raise print('box不符')

        cagetgory_id, qxd = new_box[-2], qxd_map[new_box[-1]]
        coordinates = new_box[:4]  # 替换为实际的坐标值
        # 绘制矩形框
        draw.rectangle(coordinates, outline=color_map[new_box[-1]], width=1)
        # 添加文字
        text = "{}: {}".format(name_map[cagetgory_id], qxd)  # 要显示的文字
        font = ImageFont.truetype("ADOB", 15)  # 设置字体和大小，需要有arial.ttf字体文件
        text_position = (coordinates[0], coordinates[1] - 20)  # 文字位置，根据需要调整

        # 在矩形框上绘制文字
        draw.text(text_position, text, font=font, fill=color_map[new_box[-1]])

    # 保存或显示图像
    # img.show()
    # 或者保存到文件
    img.save(save+os.path.splitext(image_path.split('/')[-1])[0]+'.png')

    original_img = read_data2Image(image_path, SliceNum)  # 重新打开原图
    processed_img = Image.open(save+os.path.splitext(image_path.split('/')[-1])[0]+'.png')  # 打开处理后的图

    # 获取两个图像的宽度和高度
    width1, height1 = original_img.size
    width2, height2 = processed_img.size

    # 创建一个新的图像，宽度是两个图像宽度之和，高度是两者中的最大高度
    new_img = Image.new('RGB', (width1 + width2, max(height1, height2)), (255, 255, 255))

    # 将原图和处理后的图粘贴到新图像上
    new_img.paste(original_img, (0, 0))
    new_img.paste(processed_img, (width1, 0))

    # 保存新图像
    new_img.save(save+os.path.splitext(image_path.split('/')[-1])[0]+'.png')


def draw_2(image_path, SliceNum, box_info, name_map, save):
    for box in box_info:
        img = read_data2Image(image_path, SliceNum)
        draw = ImageDraw.Draw(img)
        # 矩形框的坐标点列表
        new_box = []
        for item in box.split(','):
            new_box.append(int(item))

        cagetgory_id, qxd = new_box[-2], qxd_map[new_box[-1]]
        coordinates = new_box[:4]  # 替换为实际的坐标值
        # 绘制矩形框
        draw.rectangle(coordinates, outline=color_map[new_box[-1]], width=1)
        # 添加文字
        text = "{}: {}".format(name_map[cagetgory_id], qxd)  # 要显示的文字
        font = ImageFont.truetype("simhei.ttf", 15)  # 设置字体和大小，需要有arial.ttf字体文件
        text_position = (coordinates[0], coordinates[1] - 20)  # 文字位置，根据需要调整

        # 在矩形框上绘制文字
        draw.text(text_position, text, font=font, fill=color_map[new_box[-1]])

        if not os.path.exists(save+'/'+name_map[cagetgory_id]):
            os.makedirs(save+'/'+name_map[cagetgory_id])
        if not os.path.exists(save+'/'+name_map[cagetgory_id]+'/'+qxd):
            os.makedirs(save+'/'+name_map[cagetgory_id]+'/'+qxd)

        img.save(save+'/'+name_map[cagetgory_id]+'/'+qxd+'/'+os.path.splitext(image_path.split('/')[-1])[0]+'.png')

        # 将原图和处理后的图水平拼接
        original_img = read_data2Image(image_path, SliceNum)  # 重新打开原图
        processed_img = Image.open(save+'/'+name_map[cagetgory_id]+'/'+qxd+'/'+os.path.splitext(image_path.split('/')[-1])[0]+'.png')  # 打开处理后的图

        # 获取两个图像的宽度和高度
        width1, height1 = original_img.size
        width2, height2 = processed_img.size

        # 创建一个新的图像，宽度是两个图像宽度之和，高度是两者中的最大高度
        new_img = Image.new('RGB', (width1 + width2, max(height1, height2)), (255, 255, 255))

        # 将原图和处理后的图粘贴到新图像上
        new_img.paste(original_img, (0, 0))
        new_img.paste(processed_img, (width1, 0))

        # 保存新图像
        new_img.save(save+'/'+name_map[cagetgory_id]+'/'+qxd+'/'+os.path.splitext(image_path.split('/')[-1])[0]+'.png')


def gen_img(txt_path, name_map, id_map, save_path):

    with open(txt_path, 'r') as f:
        lines = f.readlines()
        for line in tqdm(lines):
            line = line.strip()
            category_id = []

            imgPath = line.split()[0].split("__")[0] + ".dcm"
            
            SliceNum = int(line.split()[0].split("__")[1])
            
            name = imgPath.split('/')[-1].split("__")[0]
            QieMian = line.split()[1]
            box = line.split()[2:]
            # 获得该标签的切面类别
            for key in id_map:
                label_id = int(box[0].split(',')[-2])
                if label_id in id_map[key]:
                    category_name = key
                    break

            for bbox in box:
                category_id.append(int(bbox.split(',')[-2]))
            
            draw_1(imgPath, SliceNum, box, name_map, save_path+'/'+category_name+'/label_show/')
            draw_2(imgPath, SliceNum, box, name_map, save_path+'/'+category_name)


if __name__ == "__main__":
    SavingPath = "D:/code/US/GI/Label/Convert/InputJson/"
    
    file_path_train = 'D:/code/US/GI/Label/Convert/Else/NewTrainInfo_DelSpa.txt'
    file_path_val = 'D:/code/US/GI/Label/Convert/Else/NewValInfo_DelSpa.txt'
    save = 'E:/Data/US/GI/Temp/LabelCheck/'
    id_map = get_IdMap('D:/code/US/GI/Label/Convert/Else/GImap.json')
    name_map = get_NameMap('D:/code/US/GI/Label/Convert/Else/GImap.json')

    for key in id_map:
        if not os.path.exists(save+key):
            os.makedirs(save+key)
        if not os.path.exists(save+key+'/label_show'):
            os.makedirs(save+key+'/label_show')

    gen_img(file_path_train, name_map, id_map, save)
    gen_img(file_path_val, name_map, id_map, save)

    print()

