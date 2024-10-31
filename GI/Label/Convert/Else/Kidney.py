# -*- coding:utf-8 -*-
# @Author  : yunxu.li@united-imaging.com
# @File    : Kidney.py
# @Time    : 2024/10/17 14:48
# @Desc    : 

from Convert import *


def KidneyFunc(ImageId):
    images, annotations = [], [] 
    # pancreas
    # \\isi-wh\US\05_SW\LabelData\ImageAnalysisAnnotation\GI\PH-TS_2D_V1.0\03_second_review_data
    # SrcPath = "E:/Data/US/GI/Abd/LabelConvertTest/PH-TS_2D_V1.0/03_second_review_data/UIH_20240820_0820-001_20240820.094540.650_m_5/"
    SrcPath = "E:/Data/US/GI/Abd/LabelConvertTest/PH-TS_2D_V1.0/03_second_review_data/"
    for file in os.listdir(SrcPath):
        FilePath = SrcPath + file + '/'
        FileId = FilePath.split('/')[-4]
        ImgId = FilePath.split('/')[-2]
        # DcmPath = FilePath + ImgId + '.dcm'
        PointNrrdPath = FilePath + ImgId + '.dcm_point.nrrd'
        LabelNrrdPath = FilePath + ImgId + '.dcm_label.nrrd'
        CriteriaExcelPath = FilePath + ImgId + '.dcm.xlsx'

        # if os.path.exists(DcmPath):
        #     DcmInfo, DcmData = ExtractDicomFileInfo(DcmPath)
        # else:
        #     print(DcmPath + " No DcmPath")
        if os.path.exists(PointNrrdPath):
            Pointdata, Pointheader = nrrd.read(PointNrrdPath)
            Width, Height, Slice = Pointdata.shape
        else:
            print(PointNrrdPath + " No PointNrrdPath")
        if os.path.exists(LabelNrrdPath):
            Labeldata, Labelheader = nrrd.read(LabelNrrdPath)
            Width, Height, Slice = Pointdata.shape
        else:
            print(LabelNrrdPath + " No labelNrrdPath")
        if os.path.exists(CriteriaExcelPath):
            CriteriaExcel = pd.read_excel(CriteriaExcelPath)
        else:
            print(CriteriaExcelPath + " No CriteriaExcelPath")

        Index = CriteriaExcel['帧号(清晰, 模糊, 不可见 对应 A, B, C)']
        SpVClass = CriteriaIndexDict["脾静脉-"+FileEng2Chinese[FileId]]

        # 不打算用图片格式 Dicom读入 不含评价的那些也是需要纳入的
        # 点 Mask 分数分了不同的信息类别，后面基于一个网络都输出出来？可以加一个或者多个头。
        for i in range(Slice):
            image = {
                "file_name": ImgId + '_' + str(i),
                "height": Height,
                "width": Width,
                "id": ImageId
            }
            # 预处理：除了必要的强度归一化之外。切片索引。放到DataLoader里。
            # TODO: 利用Matrix的Spacing信息 spacing标准化 加窗等操作
            
            annotation = {
                # keypoints
                "keypoints": [],            # 对那些没有标注的，keypoints给空列表
                "num_keypoints": 0,         # 对那些没有标注的，num_keypoints给0
                # segmentation
                "segmentation": [],         # 对那些没有标注的，segmentation给空列表
                "segmentation_class": [],   # 分割的类别。自定义字段。
                # "area": 0,                  # 这个参数其实用不到 不做更新
                # "iscrowd": 0,               # 0时segmentation为polygon，1为REL。采用默认值0.
                "image_id": ImageId,
                # category
                # 对那些没有评价的，默认的分类怎么给？同一帧的标注上面，按照当前的分类来的话，那一张图上有几个关键的评估那就有大的几类
                "category_ids": [],
                "category_scores": []      # 对那些没有评价的，暂时先给一个0 这样会和那些没给评价的区分不开 那些没给评价的分数怎么给呢？
                # "id": segmentation_id
            }

            if i + 1 in Index.values:
                if os.path.exists(PointNrrdPath):
                    Slice = Pointdata[:, :, i]
                    # 胰头胰体下分界点 1；胰头胰体上分界点 2；胰体胰尾上分界点 3；胰体胰尾下分界点 4
                    if len(np.where(Slice == 1)[0]) != 0:
                        P1Center = (np.where(Slice == 1)[0].mean(), np.where(Slice == 1)[1].mean())
                        annotation["keypoints"].append([P1Center[0], P1Center[1], i])    
                    if len(np.where(Slice == 2)[0]) != 0:
                        P2Center = (np.where(Slice == 2)[0].mean(), np.where(Slice == 2)[1].mean())
                        annotation["keypoints"].append([P2Center[0], P2Center[1], i])    
                    if len(np.where(Slice == 3)[0]) != 0:
                        P3Center = (np.where(Slice == 3)[0].mean(), np.where(Slice == 3)[1].mean())
                        annotation["keypoints"].append([P3Center[0], P3Center[1], i])    
                    if len(np.where(Slice == 4)[0]) != 0:
                        P4Center = (np.where(Slice == 4)[0].mean(), np.where(Slice == 4)[1].mean())
                        annotation["keypoints"].append([P4Center[0], P4Center[1], i])    
                    annotation["num_keypoints"] = len(annotation["keypoints"])
                
                # 将segmentation转换为coco中的格式 实质需要存的为7部分
                # 0: background
                # 1+6: pancreas 然后胰腺需要拆分胰头7 体9 尾8
                # 2：SMA    肠系膜上动脉
                # 3：IVC    下腔静脉
                # 4：SpV    脾静脉
                # 5：Ao     腹主动脉
                # 6：real pancreas 不需要纳入
                # 首先将label 6转换为1
                label6 = np.where(Labeldata[:, :, i] == 6)
                for j in range(len(label6[0])):
                    x, y = label6[0][j], label6[1][j]
                    Labeldata[x, y, i] = 1
                
                # label 1拆分头 体 尾
                # 位于胰头胰体下分界点 1 和胰头胰体上分界点 2 连线左侧的部分为胰头，赋予新标签 7
                # 位于胰体胰尾上分界点 3 和胰体胰尾下分界点 4 连线右侧的部分为胰尾，赋予新标签 8
                # 处在label 1内 但不在上述两个区域内的为胰体，赋予新标签 9
                k12 = (P2Center[0] - P1Center[0]) / (P2Center[1] - P1Center[1])
                b12 = P2Center[0] - k12 * P2Center[1]
                k34 = (P3Center[0] - P4Center[0]) / (P3Center[1] - P4Center[1])
                b34 = P4Center[0] - k34 * P4Center[1]

                label1 = np.where(Labeldata[:, :, i] == 1)
                for j in range(len(label1[0])):
                    x, y = label1[0][j], label1[1][j]
                    if y * k12 + b12 >= x:
                        Labeldata[x, y, i] = 7
                    elif y * k34 + b34 < x:
                        Labeldata[x, y, i] = 9
                    else:
                        Labeldata[x, y, i] = 8

                for count_contours in range(2, 10):
                    binary_mask = Labeldata[:, :, i] == count_contours
                    if np.sum(binary_mask) != 0:
                        contours, hierarchy = cv2.findContours(binary_mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # 根据二值图找轮廓
                        for _, contour in enumerate(contours):
                            # 求segmentation部分
                            contour = np.flip(contour, axis=0)
                            segmentation = contour.ravel().tolist()
                            annotation["segmentation"].append(segmentation)
                            annotation["segmentation_class"].append(count_contours)
                            
                # 将评分信息添加到annotation的分类信息中
                # 需要判断对应的评分是否为空。空的话，对应的类和评分就不被push
                # 首先Get帧号所在的行 
                FlipRow = np.where(Index.values == i + 1)[0][0]
                if CriteriaExcel['肠系膜上动脉'][FlipRow] in [0, 1, 2]:
                    annotation['category_ids'].append(CriteriaIndexDict['肠系膜上动脉'])
                    annotation['category_scores'].append(CriteriaExcel['肠系膜上动脉'][FlipRow])
                if CriteriaExcel['下腔静脉'][FlipRow] in [0, 1, 2]:
                    annotation['category_ids'].append(CriteriaIndexDict['下腔静脉'])
                    annotation['category_scores'].append(CriteriaExcel['下腔静脉'][FlipRow])
                if CriteriaExcel['脾静脉'][FlipRow] in [0, 1, 2]:
                    annotation['category_ids'].append(CriteriaIndexDict['脾静脉-'+FileEng2Chinese[FileId]])
                    annotation['category_scores'].append(CriteriaExcel['脾静脉'][FlipRow])
                if CriteriaExcel['腹主动脉'][FlipRow] in [0, 1, 2]:
                    annotation['category_ids'].append(CriteriaIndexDict['腹主动脉'])
                    annotation['category_scores'].append(CriteriaExcel['腹主动脉'][FlipRow])
                if CriteriaExcel['胰体'][FlipRow] in [0, 1, 2]:
                    annotation['category_ids'].append(CriteriaIndexDict['胰体'])
                    annotation['category_scores'].append(CriteriaExcel['胰体'][FlipRow]) 
                if CriteriaExcel['胰头'][FlipRow] in [0, 1, 2]:
                    annotation['category_ids'].append(CriteriaIndexDict['胰头'])
                    annotation['category_scores'].append(CriteriaExcel['胰头'][FlipRow]) 
                if CriteriaExcel['胰尾'][FlipRow] in [0, 1, 2]:
                    annotation['category_ids'].append(CriteriaIndexDict['胰尾'])
                    annotation['category_scores'].append(CriteriaExcel['胰尾'][FlipRow]) 
            
            images.append(image)
            annotations.append(annotation)
            ImageId = ImageId + 1


def Func():
    pass


if __name__ == '__main__':
    Func()

