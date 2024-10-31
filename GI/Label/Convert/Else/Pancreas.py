# -*- coding:utf-8 -*-
# @Author  : yunxu.li@united-imaging.com
# @File    : Pancreas.py
# @Time    : 2024/10/17 14:45
# @Desc    :

from Convert import *


def PancreasFunc(ImageId):
    # 胰头横切面 PH-TS 胰体横切面 PB-TS 胰尾横切面 PT-TS
    SectionPath = [
        # "//isi-wh/US/05_SW/LabelData/ImageAnalysisAnnotation/GI/PH-TS_2D_V1.0/03_second_review_data", 
        # "//isi-wh/US/05_SW/LabelData/ImageAnalysisAnnotation/GI/PH-TS_2D_V1.0/03_second_review_data", 
        # "//isi-wh/US/05_SW/LabelData/ImageAnalysisAnnotation/GI/PH-TS_2D_V1.0/03_second_review_data", 
        "E:/Data/US/GI/Abd/LabelConvertTest/PH-TS_2D_V1.0/03_second_review_data/",
        "E:/Data/US/GI/Abd/LabelConvertTest/PB-TS_2D_V1.0/03_second_review_data/",
        "E:/Data/US/GI/Abd/LabelConvertTest/PT-TS_2D_V1.0/03_second_review_data/"
    ]
    for SrcPath in SectionPath:
        # SrcPath = "E:/Data/US/GI/Abd/LabelConvertTest/PH-TS_2D_V1.0/03_second_review_data/"
        SegmentationDict = {# a['Segment0_Name']a['Segment0_Layer']a['Segment0_LabelValue'] 
            2: "肠系膜上动脉", 3: "下腔静脉", 4: "脾静脉", 5: "腹主动脉", 7: "胰头", 8: "胰体", 9: "胰尾" # 
        }
        JsonSavingPaths = []
        
        for file in os.listdir(SrcPath):
            images, annotations = [], []
            
            FilePath = SrcPath + file + '/'
            FileId = FilePath.split('/')[-4]            # PH-TS_2D_V1.0
            ImgId = FilePath.split('/')[-2]             #'UIH_20240820_0820-001_20240820.094540.650_m_5'
            JsonSavingPath = FilePath + ImgId + '.json' # 名字采用ImgId
                    
            # Read Data
            DcmPath = FilePath + ImgId + '.dcm'
            PointNrrdPath = FilePath + ImgId + '.dcm_point.nrrd'
            LabelNrrdPath = FilePath + ImgId + '.dcm_label.nrrd'
            CriteriaExcelPath = FilePath + ImgId + '.dcm.xlsx'

            if os.path.exists(DcmPath):
                DcmImg = pydicom.dcmread(DcmPath) 
                AllSliceNum = int(DcmImg.StopTrim) - int(DcmImg.StartTrim) + 1
                if AllSliceNum < 100:   
                    print(DcmPath + " Dicom SliceNum < 100")
                    # 由于mhd中截取的是后100帧 需要计算出截取前后的Z方位的索引差
                    DiffSliceIdx = 0
                else:  
                    DiffSliceIdx = AllSliceNum - 100       
            else:
                print(DcmPath + " No DcmPath")
                
            if os.path.exists(PointNrrdPath):
                Pointdata, Pointheader = nrrd.read(PointNrrdPath)
                Width, Height, Slice = Pointdata.shape
            else:
                print(PointNrrdPath + " No PointNrrdPath")
            if os.path.exists(LabelNrrdPath):
                # 很多情况是存在多通道的 CHWD 会是4维的 和三维的分开处理；Lable名不应是默认的名字 不然会读不到*header中的key；中文的key会读不到
                # reader的实现需要改写 line 264 改成 line = line.decode('utf-8', 'ignore')
                Labeldata, Labelheader = nrrd.read(LabelNrrdPath)
                Width, Height, Slice = Pointdata.shape
            else:
                print(LabelNrrdPath + " No labelNrrdPath")
            if os.path.exists(CriteriaExcelPath):
                CriteriaExcel = pd.read_excel(CriteriaExcelPath)
            else:
                print(CriteriaExcelPath + " No CriteriaExcelPath")

            Index = CriteriaExcel['帧号(清晰, 模糊, 不可见 对应 A, B, C)']

            # 不打算用图片格式 Dicom读入 不含评价的那些也是需要纳入的
            # 点 Mask 分数分了不同的信息类别，后面基于一个网络都输出出来？可以加一个或者多个头。
            for i in range(AllSliceNum):
                image = {
                    # Dicom ID + Slice Index in Origin Dicom
                    "file_name": ImgId + '_' + str(i),      # Dicom ID + Slice Index in Origin Dicom
                    "height": Height,                       # y max
                    "width": Width,                         # x max
                    "depth": AllSliceNum,                   # z max
                    "id": ImageId                           # 原始Dicom的每帧的UID，Start from 0
                }
                # 预处理：除了必要的强度归一化之外。切片索引。放到DataLoader里。
                # TODO: 利用Matrix的Spacing信息 spacing标准化 加窗等操作

                # 场景-切面用文件夹区分 例如在GI-胰腺下
                annotation = {
                    # ADD 
                    # 场景 切面
                    # keypoints
                    # 对那些没有标注的，keypoints给空列表
                    # 1. Loc中z标识在原始DCM的帧数
                    # 2. 每个改成一个字典（key值区分 用 组织-位置 例如：胰头-胰体上分界点）
                    # 3. score。标注的分数。没有标注的，给-1。
                    # 举例：{'胰头胰体下分界点': {"Loc": [x1, y1, z1], "score": score1},
                    #       '胰头胰体上分界点': {"Loc": [x2, y2, z2], "score": score2},
                    #       '胰体胰尾下分界点': {"Loc": [x3, y3, z3], "score": score3},
                    #       '胰体胰尾上分界点': {"Loc": [x4, y4, z4], "score": score4}}
                    "keypoints": {},

                    # segmentation
                    # 对那些没有标注的，segmentation给空列表。polygon，都是(y, x).
                    # 内部key用Mask的名字，value是mask的坐标点列表。
                    # score。标注的分数。没有标注的，给-1。
                    # 举例：{'MaskName1': {"Loc": [...], "score": score1},
                    #       'MaskName2': {"Loc": [...], "score": score2},
                    #       'MaskName3': {"Loc": [...], "score": score3},
                    #       'MaskName4': {"Loc": [...], "score": score4}}
                    "segmentation": {},
                    "image_id": ImageId
                }
                annotation["keypoints"]["胰头胰体下分界点"] = {}
                annotation["keypoints"]["胰头胰体上分界点"] = {}
                annotation["keypoints"]["胰体胰尾下分界点"] = {}
                annotation["keypoints"]["胰体胰尾上分界点"] = {}
                
                annotation["segmentation"]["肠系膜上动脉"] = {}
                annotation["segmentation"]["下腔静脉"] = {}
                annotation["segmentation"]["脾静脉" + "-" + FileEng2Chinese[FileId]] = {}
                annotation["segmentation"]["腹主动脉"] = {}
                annotation["segmentation"]["胰头"] = {}
                annotation["segmentation"]["胰体"] = {}
                annotation["segmentation"]["胰尾"] = {}
                
                if i + 1 - DiffSliceIdx  in Index.values:
                    if os.path.exists(PointNrrdPath):
                        Slice = Pointdata[:, :, i - DiffSliceIdx]

                        # 1 胰头胰体下分界点；2 胰头胰体上分界点；3 胰体胰尾下分界点；4 胰体胰尾上分界点
                        if len(np.where(Slice == 1)[0]) != 0:
                            P1Center = (np.where(Slice == 1)[0].mean(), np.where(Slice == 1)[1].mean())
                            annotation["keypoints"]["胰头胰体下分界点"]["Loc"] = [P1Center[0], P1Center[1], i + DiffSliceIdx]
                            annotation["keypoints"]["胰头胰体下分界点"]["score"] = -1
                        if len(np.where(Slice == 2)[0]) != 0:
                            P2Center = (np.where(Slice == 2)[0].mean(), np.where(Slice == 2)[1].mean())
                            annotation["keypoints"]["胰头胰体上分界点"]["Loc"] = [P2Center[0], P2Center[1], i + DiffSliceIdx]
                            annotation["keypoints"]["胰头胰体上分界点"]["score"] = -1
                        if len(np.where(Slice == 3)[0]) != 0:
                            P3Center = (np.where(Slice == 3)[0].mean(), np.where(Slice == 3)[1].mean())
                            annotation["keypoints"]["胰体胰尾下分界点"]["Loc"] = [P3Center[0], P3Center[1], i + DiffSliceIdx]
                            annotation["keypoints"]["胰体胰尾下分界点"]["score"] = -1
                        if len(np.where(Slice == 4)[0]) != 0:
                            P4Center = (np.where(Slice == 4)[0].mean(), np.where(Slice == 4)[1].mean())
                            annotation["keypoints"]["胰体胰尾上分界点"]["Loc"] = [P4Center[0], P4Center[1], i + DiffSliceIdx]
                            annotation["keypoints"]["胰体胰尾上分界点"]["score"] = -1

                    # 将segmentation转换为coco中的格式 实质需要存的为7部分
                    # 0: background
                    # 1+6: pancreas 然后胰腺需要拆分胰头7 体9 尾8
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

                    # label 1拆分头 体 尾
                    # 位于胰头胰体下分界点 1 和胰头胰体上分界点 2 连线左侧的部分为胰头，赋予新标签 7
                    # 位于胰体胰尾上分界点 3 和胰体胰尾下分界点 4 连线右侧的部分为胰尾，赋予新标签 8
                    # 处在label 1内 但不在上述两个区域内的为胰体，赋予新标签 9
                    k12 = (P2Center[0] - P1Center[0]) / (P2Center[1] - P1Center[1])
                    b12 = P2Center[0] - k12 * P2Center[1]
                    k34 = (P3Center[0] - P4Center[0]) / (P3Center[1] - P4Center[1])
                    b34 = P4Center[0] - k34 * P4Center[1]

                    label1 = np.where(Labeldata[:, :, i - DiffSliceIdx] == 1)
                    for j in range(len(label1[0])):
                        x, y = label1[0][j], label1[1][j]
                        if y * k12 + b12 >= x:
                            Labeldata[x, y, i - DiffSliceIdx] = 7
                        elif y * k34 + b34 < x:
                            Labeldata[x, y, i - DiffSliceIdx] = 9
                        else:
                            Labeldata[x, y, i - DiffSliceIdx] = 8

                    for count_contours in range(2, 10):
                        binary_mask = Labeldata[:, :, i - DiffSliceIdx] == count_contours
                        if np.sum(binary_mask) != 0:
                            contours, hierarchy = cv2.findContours(binary_mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # 根据二值图找轮廓
                            for _, contour in enumerate(contours):
                                # 求segmentation部分
                                contour = np.flip(contour, axis=0)
                                segmentation = contour.ravel().tolist()
                                if count_contours != 6:
                                    if count_contours == 4:
                                        annotation["segmentation"][SegmentationDict[count_contours] + "-" + FileEng2Chinese[FileId]]["Loc"] = segmentation
                                        annotation["segmentation"][SegmentationDict[count_contours] + "-" + FileEng2Chinese[FileId]]["score"] = -1
                                    else:
                                        annotation["segmentation"][SegmentationDict[count_contours]]["Loc"] = segmentation
                                        annotation["segmentation"][SegmentationDict[count_contours]]["score"] = -1

                    # 将评分信息添加到annotation。
                    # 需要判断对应的评分是否为空。空的话，对应的score就保持-1.
                    # 首先Get帧号所在的行
                    FlipRow = np.where(Index.values == i + 1 - DiffSliceIdx)[0][0]
                    for count_contours in range(2, 10):
                        if count_contours != 6:
                            if count_contours == 4:
                                if CriteriaExcel[SegmentationDict[count_contours]][FlipRow] in [0, 1, 2]:
                                    annotation["segmentation"][SegmentationDict[count_contours] + "-" + FileEng2Chinese[FileId]]["score"] = CriteriaExcel[SegmentationDict[count_contours]][FlipRow]
                            else:
                                if CriteriaExcel[SegmentationDict[count_contours]][FlipRow] in [0, 1, 2]:
                                    annotation["segmentation"][SegmentationDict[count_contours]]["score"] = CriteriaExcel[SegmentationDict[count_contours]][FlipRow]

                images.append(image)
                annotations.append(annotation)
                ImageId = ImageId + 1

            JsonWrite(JsonSavingPath, images, annotations)
            JsonSavingPaths.append(JsonSavingPath + " " + str(AllSliceNum))     # Path + Slice Num
            
        WriteListToTxt(JsonSavingPaths, SrcPath + "JsonPaths.txt")
        

def Func():
    pass


if __name__ == '__main__':
    Func()
