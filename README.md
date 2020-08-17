#author: livingthings, a fans of aragaki yui（新垣结衣）
#date:   2020.8.7
#this is about how to play this project

[python main.py --help]

流程：
1. [python main.py --listen]
    把音乐文件放入目录[./wa/music_of_gaki/]
    学习这些音乐的相关属性
    
2. [python main.py --train-exp -train-help]
    放一些正面清晰照于目录[./wa/exp_train/]
    根据提示对这些图片进行表情 “开心” “忧伤” “正常” 标签标注
    
3. [python main.py --train-exp -start]
    开始根据表情标注对表情进行学习
    
4. [python main.py --learn]
    放一些正面清晰照于目录[./wa/pic_of_gaki/]
    使用这些照片进行人脸识别的学习
    
5. [python main.py --recognize -test -sample-rate 30 -slice]
    把视频文件放入目录[./wa/video_of_gaki/]，然后执行上面的命令
    保证里面有新垣结衣出现
    大型视频的识别会花很长时间，不想等太久的话试试-fastest子命令
    
6. [python main.py --make-mv -random]
    开始生成一个随机属性的MV！
    开场白和结束语的配置文件需要放在目录[./wa/materials/]下
    生成的MV会被放到目录[./wa/output_movie/]下
    
7. [python main.py --make-album -random]
    开始生成一个随机属性的音乐相册！
    开场白和结束语的配置文件需要放在目录[./wa/materials/]下
    默认使用目录[./wa/album_of_gaki/]下的照片，你也可以指定其他目录，比如之前学习的目录
    但是指定的目录只能是[./wa/]下的
    生成的音乐相册会被放到目录[./wa/output_movie/]下

warning: The Whole Project Is Not Completed Yet! There Are A Lot Of Bugs In it
Should I be the only one who knows how to use it right now
