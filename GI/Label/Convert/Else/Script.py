# -*- coding:utf-8 -*-
# @Author  : yunxu.li@united-imaging.com
# @File    : Script.py
# @Time    : 2024/10/14 17:40
# @Desc    :

import sys
sys.path.append('D:/code/')
import io
import cv2
from pycocotools import mask
import json
from Tools.ImageIO.ImageIO import *
from Tools.TxtProcess import *
from tqdm import tqdm
import numpy as np
import shutil
import os
import pydicom



if sys.version_info[0] >= 3:
    unicode = str


# 实例的id，每个图像有多个物体每个物体的唯一id
global segmentation_id
segmentation_id = 1
# annotations部分的实现


def maskToanno(ground_truth_binary_mask, ann_count, category_id):
    contours, _ = cv2.findContours(
        ground_truth_binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # 根据二值图找轮廓
    annotations = []  # 一幅图片所有的annotatons
    # print(len(contours),contours)
    global segmentation_id
    if (len(contours) == 0):
        print("0")
    # 对每个实例进行处理
    for i, contour in enumerate(contours):
        if (len(contour) < 3):
            print("The contour does not constitute an area")
            continue
        ground_truth_area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        annotation = {
            "segmentation": [],
            "area": ground_truth_area,
            "iscrowd": 0,
            "image_id": ann_count,
            "bbox": [x, y, w, h],
            "category_id": category_id,
            "id": segmentation_id
        }
        # 求segmentation部分
        contour = np.flip(contour, axis=0)
        segmentation = contour.ravel().tolist()
        annotation["segmentation"].append(segmentation)
        annotations.append(annotation)
        segmentation_id = segmentation_id + 1
    return annotations

def DicomTagRead(filename):
    filename = 'E:/Data/US/GI/Abd/LabelConvertTest/PH-TS_2D_V1.0/03_second_review_data/UIH_20240822_0822-001_20240822.092537.688_m_17/UIH_20240822_0822-001_20240822.092537.688_m_17.dcm'
    # 读取Dicom文件
    ds = pydicom.dcmread(filename)

    # 保存某一层数据
    slice_ds = pydicom.Dataset()
    # slice_ds.file_meta = ds.file_meta           # 无效
    slice_ds.AccessionNumber = ds.AccessionNumber
    slice_ds.AcquisitionDateTime = ds.AcquisitionDateTime
    slice_ds.ActualFrameDuration = ds.ActualFrameDuration
    slice_ds.BitsAllocated = ds.BitsAllocated
    slice_ds.BitsStored = ds.BitsStored
    slice_ds.BoneThermalIndex = ds.BoneThermalIndex
    slice_ds.CineRate = ds.CineRate
    slice_ds.Columns = ds.Columns
    slice_ds.ContentDate = ds.ContentDate
    slice_ds.ContentTime = ds.ContentTime
    slice_ds.CranialThermalIndex = ds.CranialThermalIndex
    slice_ds.DerivationDescription = ds.DerivationDescription
    slice_ds.DeviceSerialNumber = ds.DeviceSerialNumber
    slice_ds.EffectiveDuration = ds.EffectiveDuration
    slice_ds.FrameDelay = ds.FrameDelay
    slice_ds.FrameTime = ds.FrameTime
    slice_ds.FrameTimeVector = ds.FrameTimeVector
    slice_ds.HighBit = ds.HighBit
    slice_ds.InstanceNumber = ds.InstanceNumber
    slice_ds.InstitutionName = ds.InstitutionName
    slice_ds.InstitutionalDepartmentName = ds.InstitutionalDepartmentName
    slice_ds.Manufacturer = ds.Manufacturer
    slice_ds.ManufacturerModelName = ds.ManufacturerModelName
    slice_ds.MechanicalIndex = ds.MechanicalIndex
    slice_ds.Modality = ds.Modality
    slice_ds.NumberOfFrames = ds.NumberOfFrames
    slice_ds.OtherPatientIDs = ds.OtherPatientIDs
    slice_ds.PatientBirthDate = ds.PatientBirthDate 
    slice_ds.PatientID = ds.PatientID
    slice_ds.PatientName = ds.PatientName
    slice_ds.PatientSex = ds.PatientSex
    slice_ds.PhotometricInterpretation = ds.PhotometricInterpretation
    slice_ds.PixelRepresentation = ds.PixelRepresentation
    slice_ds.PlanarConfiguration = ds.PlanarConfiguration
    slice_ds.PreferedPlaybackSequencing = ds.PreferedPlaybackSequencing
    slice_ds.ProcessingFunction = ds.ProcessingFunction
    slice_ds.RecommendationDisplayFrameRate = ds.RecommendationDisplayFrameRate
    slice_ds.SOPClassUID = ds.SOPClassUID
    slice_ds.SOPInstanceUID = ds.SOPInstanceUID
    slice_ds.SamplesPerPixel = ds.SamplesPerPixel
    slice_ds.SeriesDate = ds.SeriesDate
    slice_ds.SeriesInstanceUID = ds.SeriesInstanceUID
    slice_ds.SeriesNumber = ds.SeriesNumber
    slice_ds.SeriesTime = ds.SeriesTime
    slice_ds.SoftTissualThermalIndex = ds.SoftTissualThermalIndex
    slice_ds.SoftwareVersions = ds.SoftwareVersions
    slice_ds.SpecificCharacterSet = ds.SpecificCharacterSet
    slice_ds.StartTrim = ds.StartTrim
    slice_ds.StopTrim = ds.StopTrim
    slice_ds.StudyDate = ds.StudyDate
    slice_ds.StudyInstanceUID = ds.StudyInstanceUID
    slice_ds.StudyTime = ds.StudyTime
    slice_ds.TransducerData = ds.TransducerData
    slice_ds.UltrasoundColorDataPresent = ds.UltrasoundColorDataPresent
    slice_ds.default_element_format = ds.default_element_format
    slice_ds.default_sequence_element_format = ds.default_sequence_element_format
    slice_ds.indent_chars = ds.indent_chars
    slice_ds.is_decompressed = ds.is_decompressed
    slice_ds.is_implicit_VR = ds.is_implicit_VR
    slice_ds.is_little_endian = ds.is_little_endian
    slice_ds.is_original_encoding = ds.is_original_encoding
    slice_ds.is_undefined_length_sequence_item = ds.is_undefined_length_sequence_item
    slice_ds.read_encoding = ds.read_encoding
    slice_ds.read_implicit_vr = ds.read_implicit_vr
    slice_ds.read_little_endian = ds.read_little_endian
    slice_ds.timestamp = ds.timestamp

    return slice_ds


def Func():
    ################ 截取单帧Dicom Slice并配备Header的保存 ################
    import SimpleITK as sitk 
    file_name = 'E:/Data/US/GI/Abd/LabelConvertTest/PH-TS_2D_V1.0/03_second_review_data/UIH_20240822_0822-001_20240822.092537.688_m_17/UIH_20240822_0822-001_20240822.092537.688_m_17.dcm'
    
    image = sitk.ReadImage(file_name)
    image_arr = sitk.GetArrayFromImage(image) # in shape of (z, y, x, 3) 3 is for RGB
    
    image_slice_arr = np.expand_dims(image_arr[-1, :, :, :], 0) # in shape of (1, y, x, 3)
    filtered_image = sitk.GetImageFromArray(image_slice_arr)
    filtered_image.SetSpacing(image.GetSpacing())
    filtered_image.SetDirection(image.GetDirection())
    
    writer = sitk.ImageFileWriter()
    writer.KeepOriginalImageUIDOn()
    
    # Copy the meta-data except the rescale-intercept, rescale-slope为什么不拷贝？
    for k in image.GetMetaDataKeys():
        filtered_image.SetMetaData(k, image.GetMetaData(k))
    filtered_image.SetMetaData("0008|2142", '305 ')
    filtered_image.SetMetaData("0028|0008", '1 ')
    filtered_image.SetMetaData("0028|0011", '894 ')
    
    # Set relevant keys indicating the change, modify or remove private tags as needed
    filtered_image.SetMetaData("0008|0008", "DERIVED\SECONDARY")
    # Each of the UID components is a number (cannot start with zero) and separated by a '.'
    # Write to the output directory and add the extension dcm if not there, to force writing is in DICOM format.
    writer.SetFileName('E:/Data/US/GI/Abd/LabelConvertTest/PH-TS_2D_V1.0/03_second_review_data/UIH_20240822_0822-001_20240822.092537.688_m_17/UIH_20240822_0822-001_20240822.092537.688_m_17_0.dcm')
    writer.Execute(filtered_image)
        
    # #####################
    # kernel = np.ones((1, 5), np.uint8)
    # # img = cv2.imread("D:\\code\\US\\GI\\Label\\Convert\\Test.jpeg")  # 330 500 3
    # img = cv2.imread("D:\\code\\US\\GI\\Label\\Convert\\Test.jpeg", flags=0)  # 330 500
    
    # gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)  
    # ret, binary = cv2.threshold(gray,127,255,cv2.THRESH_BINARY)  
    # binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, anchor=(2, 0), iterations=5) # 330 500
    # contours, hierarchy = cv2.findContours(binary,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)  
    # cv2.drawContours(img,contours,-1,(0,0,255),3)  
    # cv2.imshow("img", img)  
    # cv2.waitKey(0)  
    # pass


if __name__ == '__main__':
    Func()
    
    # # mask图像路径
    # block_mask_path = '...'
    # block_mask_image_files = sorted(os.listdir(block_mask_path))

    # # coco json保存的位置
    # jsonPath = "..."
    # annCount = 1
    # imageCount = 1
    # # 原图像的路径， 原图像和mask图像的名称是一致的。
    # path = "..."
    # rgb_image_files = sorted(os.listdir(path))
    # if block_mask_image_files != rgb_image_files:
    #     print("error")
    # with io.open(jsonPath, 'w', encoding='utf8') as output:
    #     # 那就全部写在一个文件夹好了
    #     output.write(unicode('{\n'))
    #     # 基本信息
    #     output.write(unicode('"info": [\n'))
    #     output.write(unicode('{\n'))
    #     info = {
    #         "year": "2023",
    #         "version": "1",
    #         "contributor": "bulibuli",
    #         "url": "",
    #         "date_created": "2023-01-17"
    #     }
    #     str_ = json.dumps(info, indent=4)
    #     str_ = str_[1:-1]
    #     if len(str_) > 0:
    #         output.write(unicode(str_))
    #     output.write(unicode('}\n'))
    #     output.write(unicode('],\n'))

    #     # lisence
    #     output.write(unicode('"lisence": [\n'))
    #     output.write(unicode('{\n'))
    #     info = {
    #         "id": 1,
    #         "url": "https://creativecommons.org/licenses/by/4.0/",
    #         "name": "CC BY 4.0"
    #     }
    #     str_ = json.dumps(info, indent=4)
    #     str_ = str_[1:-1]
    #     if len(str_) > 0:
    #         output.write(unicode(str_))
    #     output.write(unicode('}\n'))
    #     output.write(unicode('],\n'))

    #     # category
    #     output.write(unicode('"categories": [\n'))
    #     output.write(unicode('{\n'))
    #     categories = {
    #         "supercategory": "polyp",
    #         "id": 1,
    #         "name": "polyp"
    #     }
    #     str_ = json.dumps(categories, indent=4)
    #     str_ = str_[1:-1]
    #     if len(str_) > 0:
    #         output.write(unicode(str_))
    #     output.write(unicode('}\n'))
    #     output.write(unicode('],\n'))

    #     # images

    #     output.write(unicode('"images": [\n'))
    #     for image in rgb_image_files:
    #         if os.path.exists(os.path.join(block_mask_path, image)):
    #             output.write(unicode('{'))
    #             block_im = cv2.imread(os.path.join(path, image))
    #             h, w, _ = block_im.shape
    #             annotation = {
    #                 "height": h,
    #                 "width": w,
    #                 "id": imageCount,
    #                 "file_name": image
    #             }
    #             str_ = json.dumps(annotation, indent=4)
    #             str_ = str_[1:-1]
    #             if len(str_) > 0:
    #                 output.write(unicode(str_))
    #                 imageCount = imageCount + 1
    #             if (image == rgb_image_files[-1]):
    #                 output.write(unicode('}\n'))
    #             else:
    #                 output.write(unicode('},\n'))
    #     output.write(unicode('],\n'))

    #     # 写annotations
    #     output.write(unicode('"annotations": [\n'))
    #     for i in range(len(block_mask_image_files)):
    #         if os.path.exists(os.path.join(path, block_mask_image_files[i])):
    #             block_image = block_mask_image_files[i]
    #             # print(block_image)
    #             # 读取二值图像
    #             block_im = cv2.imread(os.path.join(
    #                 block_mask_path, block_image), 0)
    #             _, block_im = cv2.threshold(
    #                 block_im, 100, 1, cv2.THRESH_BINARY)
    #             if not block_im is None:
    #                 block_im = np.array(
    #                     block_im, dtype=object).astype(np.uint8)
    #                 block_anno = maskToanno(block_im, annCount, 1)
    #                 # print(block_image,len(block_anno))
    #                 for b in block_anno:
    #                     str_block = json.dumps(b, indent=4)
    #                     str_block = str_block[1:-1]
    #                     if len(str_block) > 0:
    #                         output.write(unicode('{\n'))
    #                         output.write(unicode(str_block))
    #                         if (block_image == rgb_image_files[-1] and b == block_anno[-1]):
    #                             output.write(unicode('}\n'))
    #                         else:
    #                             output.write(unicode('},\n'))
    #                 annCount = annCount + 1
    #             else:
    #                 print(block_image)

    #     output.write(unicode(']\n'))
    #     output.write(unicode('}\n'))

    # Func()
