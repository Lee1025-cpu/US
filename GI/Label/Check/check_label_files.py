# 筛选标注文件夹中不合规文件


import os
import SimpleITK as sitk
import nrrd
from tqdm import tqdm
import openpyxl


def PlaneCheck(file_name, p):
    err_name, err_value = [], []
    files_03 = os.listdir(p)
    for file in tqdm(files_03):
        p2 = p+file+'/'
        dcm_files = os.listdir(p2)

        label_frame_li = []
        dcm = False
        xlsx = False
        mhd = False
        nrrd_ = False
        for item in dcm_files:
            
            if item[-3:] == 'dcm':
                name = item.split('.dcm')[0]
                dcm = True

            if item[-3:] == 'mhd':
                img = sitk.ReadImage(p2+item)
                img_arr = sitk.GetArrayFromImage(img)
                img_frame = img_arr.shape[0]
                mhd = True

            if item[-4:] == 'nrrd':
                mask, mask_info = nrrd.read(p2+item)
                # label_frame = mask.shape[-1]
                label_frame_li.append(mask.shape[-1])
                nrrd_ = True

            if item[-4:] == 'xlsx':
                xlsx = True

        if dcm:
            pass
        else:
            err_name.append(file)
            err_value.append('dcm不存在')
        
        if mhd:
            pass
        else:
            img_frame = None
            err_name.append(file)
            err_value.append('mhd不存在')

        if nrrd_:
            if mhd:
                try:
                    for label_frame in label_frame_li:
                        if img_frame == label_frame:
                            continue
                        else:
                            err_name.append(file)
                            err_value.append('mhd与nrrd尺寸不匹配')
                except:
                    pass

        else:
            label_frame_li = None
            err_name.append(file)
            err_value.append('nrrd不存在')
        
        if xlsx:
            pass
        else:
            err_name.append(file)
            err_value.append('xlsx不存在')
        
    workbook = openpyxl.Workbook()
    # 获取默认的工作表
    sheet = workbook.active
    for i, name in enumerate(err_name):
        sheet.append([name, err_value[i]])
    # 保存工作簿
    workbook.save('D:/code/US/GI/Label/Check/Result1/{}_Error_Save.xlsx'.format(file_name))


if __name__ == '__main__':
    file_names = ["PH-TS_2D_V1.0",
                  "PB-TS_2D_V1.0",
                  "PT-TS_2D_V1.0",
                  "PH-LS_2D_V1.0",
                  "SP-LA_2D_V1.0",
                  "LK-LA_2D_V1.0",
                  "RK-LA_2D_V1.0",
                  "LK-SA_2D_V1.0",
                  "RK-SA_2D_V1.0",
                  "BL-TS_2D_V1.0",
                  "BL-LS_2D_V1.0"]
    for file_name in file_names:
        p = '//isi-wh/US/05_SW/LabelData/ImageAnalysisAnnotation/GI/{}/03_second_review_data/'.format(file_name)
        PlaneCheck(file_name, p)