# -*- coding:utf-8 -*-
# @Author  : yunxu.li@united-imaging.com
# @File    : SitkDcmWrt.py
# @Time    : 2024/10/17 09:37
# @Desc    : 

import os
import sys
sys.path.append('D:/code/')

import numpy as np
from tqdm import tqdm
from Tools.TxtProcess import *
from Tools.ImageIO.ImageIO import *
import SimpleITK as sitk
import numpy as np
import pydicom


def ExtractDicomFileInfo(filename):
    """
    提取Dicom文件的tag信息
    input :文件名
    output:相关信息
    """
    info = {}
    
    dcm = pydicom.read_file(filename)
    info["PatientID"] = dcm.PatientID               # 患者ID
    info["PatientName"] = dcm.PatientName           # 患者姓名
    info["PatientBirthData"] = dcm.PatientBirthData # 患者出生日期
    info["PatientAge"] = dcm.PatientAge             # 患者年龄
    info['PatientSex'] = dcm.PatientSex             # 患者性别
    info['StudyID'] = dcm.StudyID                   # 检查ID
    info['StudyDate'] = dcm.StudyDate               # 检查日期
    info['StudyTime'] = dcm.StudyTime               # 检查时间
    info['InstitutionName'] = dcm.InstitutionName   # 机构名称
    info['Manufacturer'] = dcm.Manufacturer         # 设备制造商
    info['StudyDescription']=dcm.StudyDescription   # 检查项目描述
    dcm_data = dcm.pixel_array
    
    return info, dcm_data

def ReadandWrtSliceDcmWithTag(file_name, SavingPath):
    if not os.path.exists(SavingPath):
        os.makedirs(SavingPath)
    
    image = sitk.ReadImage(file_name)
    image_arr = sitk.GetArrayFromImage(image) # in shape of (z, y, x, 3) 3 is for RGB
    file_id = file_name.split('/')[-1][:-4]
    
    for SliceNum in range(image_arr.shape[0]):
        # SliceNum = 0      # Tag中的帧数是1为起始的。这边是0为起始的。
        image_slice_arr = np.expand_dims(image_arr[SliceNum, :, :, :], 0) # in shape of (1, y, x, 3)
        filtered_image = sitk.GetImageFromArray(image_slice_arr)
        filtered_image.SetSpacing(image.GetSpacing())
        filtered_image.SetDirection(image.GetDirection())
        
        writer = sitk.ImageFileWriter()
        writer.KeepOriginalImageUIDOn()
        
        # Copy the meta-data(仅非私有Tag)
        for k in image.GetMetaDataKeys():
            filtered_image.SetMetaData(k, image.GetMetaData(k))
        # 单帧保存需要设置起始帧和结束帧。
        filtered_image.SetMetaData("0008|2142", str(SliceNum + 1) + ' ')    # Start Trim
        filtered_image.SetMetaData("0008|2143", str(SliceNum + 1) + ' ')    # Stop Trim
        filtered_image.SetMetaData("0028|0008", '1 ')                       # NUmber of frames

        # Write to the output directory and add the extension dcm if not there, to force writing is in DICOM format.
        writer.SetFileName(SavingPath + file_id + "_" + str(SliceNum) + '.dcm')
        writer.Execute(filtered_image)
    

if __name__=="__main__":
    ################ 截取单帧Dicom Slice并配备Header的保存 ################
    file_name = 'E:/Data/US/GI/Abd/LabelConvertTest/PH-TS_2D_V1.0/03_second_review_data/UIH_20240820_0820-001_20240820.094540.650_m_5/UIH_20240820_0820-001_20240820.094540.650_m_5.dcm'
    SavingPath = 'E:/Data/US/GI/Abd/LabelConvertTest/PH-TS_2D_V1.0/03_second_review_data/UIH_20240820_0820-001_20240820.094540.650_m_5/SliceDcm/'
    ReadandWrtSliceDcmWithTag(file_name, SavingPath)

    
