功能：
    将标注文件转换为json格式，并输出标注文件路径以及转换日志


快速上手：
    
    Step1. 得到每个切面每个文件夹的标注文件。
        Vscode打开US文件夹，并安装依赖库。
    
        1. 创建虚拟环境并安装依赖库：
            cd到US路径层级
            conda create --name <env> --file .\requirements.txt -y
            conda activate <env>

        2. 准备配置文件：
            请参考：
                https://uih.feishu.cn/docx/Or0GdfXArosRo8xneK5c0olynVg
            并修改配置文件
                \US\GI\Label\Convert\InputJson\LiverGallbladderWithoutStartFrame.json
            中的相关信息。

            StartFrame信息：
                如果需要作为输入还原标注在Dicom的帧数，请准备，并修改StartFrame。可以参考
                    方式1 \US\GI\Label\Convert\TestData\GI_Abdomen_demo.json
                    方式2 \US\GI\Label\Convert\TestData\GI_Abdomen_demo1.json 和 \US\GI\Label\Convert\TestData\GI_Abdomen_demo.json
                如果不需要，请参考
                    \US\GI\Label\Convert\TestData\GI_Abdomen_demo2.json
                
            注：程序会对配置文件做基本检查，如果配置文件有误，会提示用户修改。相关变量的合法性需要用户自己保证。

        3. 入口文件：
            \US\GI\Label\Convert\Main.py
            直接运行，并根据提示输入配置文件路径。
            例如输入：D:\code\US\GI\Label\Convert\InputJson\LiverGallbladderWithoutStartFrame.json

        4. 检查输出：
            在FilePath下，存在转换之后的标注文件和转换日志。例如：
                \US\GI\Abd\LabelConvertTest\LL-AA_2D_V2.0\03_second_review_data
                    \UIH_20240718_0718-001_20240718.102728.977_m_1\UIH_20240718_0718-001_20240718.102728.977_m_1.json
                    \UIH_20240722_0722-001_20240722.101806.951_m_1\UIH_20240722_0722-001_20240722.101806.951_m_1.json
                    \UIH_20240722_0722-003_20240722.150934.827_m_1\UIH_20240722_0722-003_20240722.150934.827_m_1.json
                    \UIH_20240722_0722-003_20240722.192445.712_m_1\UIH_20240722_0722-003_20240722.192445.712_m_1.json
                    ...
                    \AnnaConvertLog.txt
                    \JsonPaths.txt
            先检查\AnnaConvertLog.txt，查看是否有错误信息。保证无错误信息后，检查\JsonPaths.txt和其他.json文件。
    
    Step2. 提供Train和Val的Ids

        参考：
            单个切面的所有文件夹名字：\US\GI\Label\Convert\Else\AllIds\
            所有切面的训练和验证的Ids：
                \US\GI\Label\Convert\Else\TrainIds.txt
                \US\GI\Label\Convert\Else\ValIds.txt

        每个切面的Train和Val按照文件夹进行4:1划分，TrainIds.txt和ValIds.txt分别为所有切面的训练和验证的Ids.

    Step3. 利用CreateInfo.py生成Info.txt
        
        \US\GI\Label\Convert\Else\CreateInfo.py
        Step2中的Ids会作为Step3的输入。


