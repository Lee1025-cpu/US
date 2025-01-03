# -*- coding:utf-8 -*-
# @Author  : yunxu.li@united-imaging.com
# @File    : Main.py
# @Time    : 2024/10/14 10:17
# @Desc    :

from JsonProcess import *
from General import *


def Step1(NeedSkip):
    if not NeedSkip:    
        JsonReadPath = input("请输入配置文件路径：\n")
        # like JsonReadPath = "D:/code/US/GI/Label/Convert/TestData/GI_Abdomen_demo.json"
        # or JsonReadPath = "D:\code\US\GI\Label\Convert\TestData\GI_Abdomen_demo.json"
        
        json_data = JsonRead(JsonReadPath)
        GeneralFunc(json_data)


def Step2():
    # 默认输出的3个Json放在FilePath下
    FilePath = input("请输入dicom文件保存路径：\n")
    # like FilePath = "\\isi-wh\US\05_SW\LabelData\ImageAnalysisAnnotation\GI\LL-AA_2D_V2.0\03_second_review_data"
    TrainNames = ReadTxtToList(input("请输入TrainNames文件路径：\n"))
    # like TrainNames = "D:\code\US\GI\Label\Convert\TVTInfo\LL-AA_2D_V2.0\Train.txt"
    ValNames = ReadTxtToList(input("请输入ValNames文件路径：\n"))
    TestNames = ReadTxtToList(input("请输入TestNames文件路径：\n"))
    # like ValNames = "D:\code\US\GI\Label\Convert\TVTInfo\LL-AA_2D_V2.0\Val.txt"
    # like ServerSavingPath = "/home/us_groups/Data/Abdomen/20240930/肝左叶经腹主动脉矢状面/UIH_2024.07-2024.08批次"
    MakeJsonandTxt(FilePath, TrainNames, ValNames, TestNames)
    

if __name__ == '__main__':
    # Step1：根据输入的配置文件先在每个Dcm的文件夹路径下生成对应的Json文件
    NeedSkip1 = False
    Step1(NeedSkip1)
    
    # Step2：根据TVTInfo中的TrainNames，ValNames，TestNames分别生成对应的Json文件
    # Step2()
    
