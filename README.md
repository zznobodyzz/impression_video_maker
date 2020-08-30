注：这就是写着玩的东西，有不少bug，请不要尝试pull下去运行。。。
传上来仅仅是为了备份。。。

#author: livingthings, a crazy fans of aragaki_yui
#data:   2020.8.7
#this text is about how to build an mv of aragaki yui
#[Ne pas perdre espoir Cest mon seul desir]

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
    
5. [python main.py --recognize -fuzzy -sample-rate 1 -slice -slice-size 6]
    把视频文件放入目录[./wa/video_of_gaki/]
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
    
    
    
    
workflow:
1. [python main.py --listen]
    put some musics into folder [./wa/music_of_gaki/]
    learn music
    
2. [python main.py --train-exp -train-help]
    put some front-clearly pictures of gaki into folder [./wa/exp_train/]
    follow as prompt to mark "happy" "blue" "normal" on each pictures
    
3. [python main.py --train-exp -start]
    let the program start learning these picture with express you already marked
    
4. [python main.py --learn]
    put some front-clearly pictures into folder [./wa/pic_of_gaki/]
    let the program start learning aragaki's face by these pictures
    
5. [python main.py --recognize -fuzzy -sample-rate 1 -slice -slice-size 6]
    put some videos into folder [./wa/video_of_gaki/]
    make sure they are all with aragaki
    large videos will take a long time, try -fastest if you want to wait shorter
    
6. [python main.py --make-mv -random]
    make a mv with random parameters !
    opening and ending materials need to be put into folder [./wa/materials/]
    the generated movie will be at folder [./wa/output_movie/]
    
7. [python main.py --make-album -random]
    make a music album with random parameters !
    opening and ending materials need to be put into folder [./wa/materials/]
    default load pictures in folder [./wa/album_of_gaki/], you can specify this
    but must under the main folder [./wa/]
    the generated music album will be at folder [./wa/output_movie/]
