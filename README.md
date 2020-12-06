声明:写着玩的东西,可能有不少bug  
    人脸识别采用face_recognition开源库,感谢原作者  
    face_recognition项目地址：https://github.com/ageitgey/face_recognition  
    感谢python社区  
  
#author          : livingthings  
#date            : 2020.8.7  
#last update time: 2020.10.24  
#this text is about how to build an mv of aragaki yui  
#[Ne pas perdre espoir, Cest mon seul desir]  
  
  
  
********配置文件********  
config.ini  
内附详细说明  
************************  
  
  
**********流程**********  
(人脸识别第4-5步):  
1.  把音乐文件放入目录[./wa/music_of_gakki/]  
    输入[python main.py --listen],学习这些音乐的相关属性  
    命令行参数:  
        [-rescan] 强制重新扫描目录下的所有音乐文件  
        [-manual-beat] 播放音乐并要求手动设置节拍点,播放音乐的同时按回车,每按一次记录一个节拍点  
    
    
2.  (可选)放一些正面清晰照于目录[./wa/exp_train/]  
    输入[python main.py --train-exp -train-help]  
    根据提示对这些图片进行表情标签标注  
    命令行参数:  
        [-max-pic-num <个数>] 指定一次操作最多标注多少张图片  
        [-use-slice <slice目录>] 从指定目录里面选视频素材当做图片进行标注(未完善)  
        [-use-learn-pic] 从./wa/pic_of_gakki/目录选图片进行标注  
    
    
3.  (可选)开始根据表情标注对表情进行学习  
    [python main.py --train-exp -start]  
    
    
4.  放一些正面清晰照于目录[./wa/pic_of_gakki/]  
    输入[python main.py --learn]  
    使用这些照片进行人脸识别的学习  
    命令行参数:  
        [-rescan] 强制重新扫描目录下的所有图片  
    
    
5.  把视频文件放入目录[./wa/video_of_gakki/]  
    输入[python main.py --recognize]  
    利用人脸识别进行视频裁剪,产生Gakki的片段  
    命令行参数:  
        [-mode <fuzzy|fastest|full|scene>]  
            fuzzy: 模糊查找,速度比较快,但是可能会漏掉一些帧或者片段  
            fastest: 最快,但是最容易漏  
            full: 最慢,逐帧识别,适用于非常短,变化非常快的视频  
            scene: 场景识别(推荐),利用场景识别减少人脸识别次数,提高速度,并使生成的片段更完整流畅  
        [-sample-rate <秒>] 采样率,单位为秒,推荐1  
        [-slice-path <目录>] 裁剪片段存放目录,不存在则创建(wa目录下)  
    
    
6.  输入[python main.py --slice-process]  
    对裁剪的片段进行二次处理  
    命令行参数:  
        范围化参数:  
            [-slice-size-range <最小-最大>] 单位为秒,满足时间长度的片段被选中  
            [-feature <字符串>] 文件名包含该关键信息的片段被选中  
            [-slice-path <目录>] 指定目录的片段被选中  
        功能性参数:  
            [-cut-scene] 通过场景识别裁剪不同场景  
            [-cut-slice <秒>] 把选中的片段只保留前n秒  
            [-slow-slice <秒>] 把选中的片段慢放到n秒  
            [-cut-face] 识别选中的片段中人脸出现的时间点,只保留该时间点之后的部分  
        一般参数:  
            [-scan <info|face|express -mode <auto|manual>>] 调整数据库,以当前选中的片段为基准,扫描参数,人脸大小,表情(可选手动)  
            [-get-slice-length <表情>] 以当前选中的片段为基准,获取该表情片段的总长度  
    
    
7.  输入[python main.py --make-mv]  
    生成剪辑视频  
    命令行参数:  
        范围化参数:  
            [-feature <字符串>] 文件名包含该关键信息的片段被选中  
            [-express <表情>] 之前识别成此表情的片段被选中  
            [-slice-path <目录...>] 指定目录的片段被选中,可多选,空格隔开  
            [-slice-size-range <最小-最大>] 单位为秒,满足时间长度的片段被选中  
            [-face-size <百分比不加百分号>] 满足面部大小占总分辨率百分比片段被选中  
        功能性参数:  
            [-caption-height <百分比>] 把底部像素高度减掉,用于去除字幕  
            [-beat-mode] 以音乐节拍作为片段转场时机  
            [-beat-rate <秒>] 保证采样的节拍点间隔大于n秒  
            [-no-repeat] 保证同一个片段不会使用超过一次  
            [-multi-mode <follow|no>] follow:根据指定的多个目录进行横向分屏对比展示视频的生成  
            [-music-only -music-bg <文件名特征>] 用于自制的音乐  
        一般参数:  
            [-music <文件名特征>] 指定背景音乐,必须是扫描过的  
            [-time <秒>] 指定生成视频长度  
            [-lrc <文件名特征>] 歌词配置文件名(json格式),需要放在./wa/material目录下  
            [-music <文件名特征>] 指定背景音乐,必须是扫描过的  
            [-time <秒>] 指定生成视频长度  
            [-title <文件名>] 生成视频名字  
            [-opconf <文件名特征>] 开场片段配置文件(json格式),需要放在./wa/material目录下  
            [-edconf <文件名特征>] 结束片段配置文件(json格式),需要放在./wa/material目录下  
************************  
  
   
********待完善点********  
1.数据库简单的用了pickle,操作不是很方便,计划后续换成sqlite  
2.有那么一点想做成windows程序,或者服务器部署,不过工作量太大,过两年再说  
3.爬虫爬原视频的功能遥遥无期了（瘫）  
************************
