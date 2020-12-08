import sys
from log import Log
import numpy as np
from utils import *
from recognize import Rec
from rec_express import RecExp
from music import Mus
from make_movie import Mov
from make_album import Alb
from painter import Painter
#from catch_aragaki import Cat
from config import CfgDecoder

Cfg = CfgDecoder()
log = Log()
recexp = RecExp(log, Cfg)
rec = Rec(log, recexp, Cfg)
mus = Mus(log, Cfg)
mov = Mov(log, rec, mus, Cfg)
alb = Alb(log, recexp, mus, Cfg)
#cat = Cat()



def print_help():
    print("usage:\n" \
                "\t--catch        ---    try to catch aragaki's pictures and videos automatically\n" \
                "\t                      the params are as follows:\n" \
                "\t                          [-picture]   ---   try to find aragaki's pictures on the internet\n" \
                "\t                          [-video]     ---   try to find aragaki's video on the internet\n" \
                "\t--learn        ---    load picture for recognize\n" \
                "\t                      the params are as follows:\n" \
                "\t                          [-rescan]    ---   rebuild database\n"
                "\t--recognize    ---    generate video slices\n" \
                "\t                      the params are as follows:\n" \
                "\t                          [-mode <fuzzy|fastest|full|scene>]\n" \
                "\t                          [-sample-rate <num_of_seconds>]   ---  for fuzzy/fastest mode it means process each n seconds, for full mode it means process each n frames\n" \
                "\t--listen       ---    load mp3 music for generate mv and album\n" \
                "\t                      the params are as follows:\n" \
                "\t                          [-rescan]    ---   rebuild database\n" \
                "\t                          [-manual-beat] ---   you want to set beat manually\n"
                "\t--train-exp    ---    train express recognition by given dataset\n" \
                "\t                      the params are as follows:\n" \
                "\t                          [-train-help]    --- a helping tool to help you build your own dataset for express recognition\n" \
                "\t                          [-use-learn-pic] --- use --learn command pictures\n" \
                "\t                          [-use-slice <slice-folder>]     --- use slice\n" \
                "\t                          [-max-pic-num <max_num_of_picture_you_want_to_mark_at_on_time>]\n" \
                "\t                          [-start]         --- start training\n" \
                "\t--slice-pocess ---    do process on current slices\n" \
                "\t                      the params are as follows:\n" \
                "\t                          [-cut-scene] ---  searching for given start gragh and end graph and cut the frames between them\n" \
                "\t                          [-cut-slice <cut_to_n_seconds>] --- longer than n seconds' slices will be cut to n seconds\n" \
                "\t                          [-slow-slice] --- generate a slice's slow version" \
                "\t                          [-cut-face]  --- \n" \
                "\t                          [-feature    <only_slice_with_this_in_name_will_be_picked>]\n" \
                "\t                          [-slice-size-range <min-max>]\n" \
                "\t                          [-get-slice-length <express_normal_happy_blue_default>]\n" \
                "\t                          [-scan <info|face|express -mode <auto|manual>>]    ---  rebuild database\n" \
                "\t                          [-slice-path <folder>] --- process this slice folder\n" \
                "\t--make-mv      ---    make an mv with specified params\n" \
                "\t                      the params are as follows:\n" \
                "\t                          [-random]  ---   generate a random mv with a random mp3 bgm\n" \
                "\t                          [-music    <mp3_file_path>]\n" \
                "\t                          [-time     <length_in_seconds_of_mv>]\n" \
                "\t                          [-all]     ---   make a full mv by all slices\n" \
                "\t                          [-feature  <only_slice_with_this_in_name_will_be_picked>]"
                "\t                          [-title    <output_file_name_of_mv>]\n" \
                "\t                          [-opconf   <a_json_file_name_with_opening_configurations_in_it>]\n" \
                "\t                          [-edconf   <a_json_file_name_with_ending_configurations_in_it>]\n" \
                "\t                          [-no-repeat]  --- do not allow same slice appeared several times\n" \
                "\t                          [-express  <normal|happy|blue|default>]\n" \
                "\t                          [-beat-mode]  ---  generation will concern about the music beats\n" \
                "\t                          [-beat-rate  <frequence of beat(fast if small)>]\n" \
                "\t                          [-slice-size <slice_seconds>] --- only slice more than <slice-size> will picked\n" \
                "\t                          [-face-size <face_size_percent>] --- only face bigger than <face-size> will picked\n" \
                "\t                          [-lrc     <lrc-json>] --- use this id to get lrc and append lrc to the video\n" \
                "\t                          [-caption-height <n-pixel>] --- cut the n pixel of the bottom\n" \
                "\t                          [-multi-mode <follow|no>] --- will pick up slices from multi folder, and the whole mv will split to multi parts in width\n" \
                "\t                          [-slice-path <folder1> <folder2>...] --- will pick up slices from multi folder, and the whole mv will split to multi parts in width\n" \
                "\t                          [--video-only]"
                "\t--album-learn  ---    learn pictures for album making, must have an initialized express recognizer\n" \
                "\t                      the params are as follows:\n" \
                "\t                          [-folder <picture_path>]\n" \
                "\t                          [-rescan]  ---   rebuild database\n"
                "\t--make-album   ---    make an music album with specified params\n" \
                "\t                      the params are as follows:\n" \
                "\t                          [-random]  ---   generate a random album with a random mp3 bgm\n" \
                "\t                          [-music    <mp3_file_path>]\n" \
                "\t                          [-pic-num  <how_many_picture_you_want_to_use>]\n" \
                "\t                          [-interval <seconds_of_each_picture_exists>]\n" \
                "\t                          [-express  <normal|happy|blue|default>]\n" \
                "\t                          [-allow-repeat] --- allow same picture appeared several times\n" \
                "\t                          [-opconf   <a_json_file_name_with_opening_configurations_in_it>]\n" \
                "\t                          [-edconf   <a_json_file_name_with_ending_configurations_in_it>]\n" \
                "\t                          [-bggr <a background picture>]\n" \
                "\t                          [-trans-mode <fade|topin|bottomin|leftin|rightin|random>]\n" \
                "\t                          [-bgco <background color>] --- if -bggr is not specified, rgb format like [255,255,255]\n" \
                "\t                          [-beat-mode]  ---  generation will concern about the music beats\n" \
                "\t                          [-beat-rate  <frequence of beat(fast if big)>]\n" \
                "\t                          [-time     <length_in_seconds_of_mv>] --- after beat-mode\n" \
                "\t--test        ---     some commands for test\n" \
                "\t                      the params are as follows:\n" \
                "\t                          [-test-oped <a_json_file_name>] --- test an op or ed json file's effect\n" \
                "\t                          [-test-lrc <a_json_file_name>] --- test an lrc json file's effect\n" \
                "\t                          [-width <pixel>] --- test window's width\n" \
                "\t                          [-height <pixel>] --- test window's height\n")

def get_make_mv_random_commands():
    result = dict()
    result["music"] = mus.get_random_music()
    if result["music"] == None:
        log.log("get_make_mv_random_commands", "no music to choose, please input music first(with command --listen)")
        return None
    #at least need 10 seconds movie slice
    time = rec.get_movie_slices_total_length()
    if time < 10:
        log.log("get_make_mv_random_commands", "not enough slices to choose, please input slices first, at least 10 seconds please(with command --recognize)")
        return None
    result["time"] = 0
    result["title"] = "for_aragaki_mv"
    result["opconf"] = None
    result["edconf"] = None
    result["beat-mode"] = False
    result["all-mode"] = False
    result["no-repeat"] = False
    result["lrc"] = None
    result["caption-height"] = 0
    result["face-size"] = 0
    result["multi-mode"] = "nofollow"
    result["slice-path"] = []
    expresses = ["normal","happy","blue"]
    express_num = len(expresses)
    for i in range(express_num):
        result["express"] = get_random_s(expresses)
        time = rec.get_movie_express_slices_length(result["express"], rescan = False)
        if time < result["time"]:
            log.log("get_make_mv_random_commands", "random express is %s, but there is not enough slices, trying another")
            expresses.remove(result["express"])
            result["express"] = ""
        else:
            break
    if result["express"] == "":
        log.log("get_make_mv_random_commands", "using default express")
        result["express"] = "default"
    return result
    
def get_make_album_random_commands():
    result = dict()
    result["music"] = mus.get_random_music()
    if result["music"] == None:
        log.log("get_make_album_random_commands", "no music to choose, please input music first(with command --listen)")
        return None
    pic_num = alb.get_picture_nums()
    if pic_num < 10:
        log.log("get_make_album_random_commands", "not enough pictures to choose, please input pictures first, at least 10 pictures please")
    result["pic-num"] = get_random_i(10, 30 if pic_num > 30 else pic_num)
    result["interval"] = 5
    result["title"] = "for_aragaki_album"
    result["feature"] = ""
    painter = Painter("./wa/output_movie/", log, Cfg)
    result["opconf"] = None
    result["edconf"] = None
    result["allow-repeat"] = False
    result["bggr"] = painter.get_random_gr()
    result["bgco"] = "[255,255,255]"
    result["beat-mode"] = False
    result["beat-rate"] = 0
    result["time"] = 0
    result["trans-mode"] = "random"
    expresses = ["normal","happy","blue"]
    express_num = len(expresses)
    for i in range(express_num):
        result["express"] = get_random_s(expresses)
        nums = alb.get_pic_express_num(result["express"], rescan = False)
        if nums < result["pic-num"]:
            log.log("get_make_album_random_commands", "random express is %s, but there is not enough pictures, trying another")
            expresses.remove(result["express"])
            result["express"] = ""
        else:
            break
    if result["express"] == "":
        log.log("get_make_album_random_commands", "using default express")
        result["express"] = "default"
    return result
    
def get_make_mv_commands(argvs, index, length):
    #default values
    result = {"music":[], "time":0, "title":"for_aragaki", "opconf":None, \
                "edconf":None, "express":"default", \
                "beat-mode":False, "slice-size-range":"0-255", "beat-rate":2, "all-mode":False, \
                "no-repeat":False, "feature":"", "lrc":None, "caption-height":0, "face-size":0, \
                "multi-mode":"no", "slice-path":[],"video-only":False, "music-bg":None}
    if index + 1 == length:
        log.log("get_make_mv_commands", "not enough parameters")
        return None
    argvs = argvs[index + 1:]
    if "-music" in argvs:
        result["music"] = get_argvs(argvs, argvs.index("-music"), result["music"])
    if "-time" in argvs:
        result["time"] = get_argv(argvs, argvs.index("-time"), result["time"])
    if "-all" in argvs:
        result["all-mode"] = True
    if "-no-repeat" in argvs:
        result["no-repeat"] = True
    if "-title" in argvs:
        result["title"] = get_argv(argvs, argvs.index("-title"), result["title"])
    if "-feature" in argvs:
        result["feature"] = get_argv(argvs, argvs.index("-feature"), result["feature"])
    if "-opconf" in argvs:
        result["opconf"] = get_argv(argvs, argvs.index("-opconf"), result["opconf"])
    if "-edconf" in argvs:
        result["edconf"] = get_argv(argvs, argvs.index("-edconf"), result["edconf"])
    if "-express" in argvs:
        result["express"] = get_argv(argvs, argvs.index("-express"), result["express"])
    if "-lrc" in argvs:
        result["lrc"] = get_argvstr(argvs, argvs.index("-lrc"), result["lrc"])
    if "-beat-mode" in argvs:
        result["beat-mode"] = True
        if "-beat-rate" in argvs:
            result["beat-rate"] = get_argv(argvs, argvs.index("-beat-rate"), result["beat-rate"])
    if "-slice-size-range" in argvs:
        result["slice-size-range"] = get_argv(argvs, argvs.index("-slice-size-range"), result["slice-size-range"])
        result["slice-size"] = int(result["slice-size-range"].split("-")[0])
        result["slice-max-size"] = int(result["slice-size-range"].split("-")[1])
    if "-face-size" in argvs:
        result["face-size"] = get_argv(argvs, argvs.index("-face-size"), result["face-size"])
    if "-caption-height" in argvs:
        result["caption-height"] = get_argv(argvs, argvs.index("-caption-height"), result["caption-height"])
    if "-multi-mode" in argvs:
        result["multi-mode"] = get_argv(argvs, argvs.index("-multi-mode"), result["multi-mode"])
    if "-slice-path" in argvs:
        result["slice-path"] = get_argvs(argvs, argvs.index("-slice-path"), result["slice-path"])
    if "-video-only" in argvs:
        result["video-only"] = True
    return result
    
def get_make_album_commands(argvs, index, length):
    #default values
    result = {"music":None, "pic-num":0, "title":"for_aragaki", "opconf":None, \
                "edconf":None, "express":"default", \
                "allow-repeat":False, "interval":5, "bggr":None, "bgco":"[255,255,255]", \
                "beat-mode":False, "time":0, "beat-rate":4, "trans-mode":"random"}
    if index + 1 == length:
        log.log("get_make_album_commands", "not enough parameters")
        return None
    argvs = argvs[index + 1:]
    if "-music" in argvs:
        result["music"] = get_argv(argvs, argvs.index("-music") ,result["music"])
    if "-pic-num" in argvs:
        result["pic-num"] = get_argv(argvs, argvs.index("-pic-num"), result["pic-num"])
    if "-title" in argvs:
        result["title"] = get_argv(argvs, argvs.index("-title"), result["title"])
    if "-opconf" in argvs:
        result["opconf"] = get_argv(argvs, argvs.index("-opconf"), result["opconf"])
    if "-edconf" in argvs:
        result["edconf"] = get_argv(argvs, argvs.index("-edconf"), result["edconf"])
    if "-express" in argvs:
        result["express"] = get_argv(argvs, argvs.index("-express"), result["express"])
    if "-allow-repeat" in argvs:
        result["allow-repeat"] = True
    if "-interval" in argvs:
        result["interval"] = get_argv(argvs, argvs.index("-interval"), result["interval"])
    if "-bggr" in argvs:
        result["bggr"] = get_argv(argvs, argvs.index("-bggr"), result["bggr"])
    if "-bgco" in argvs:
        result["bgco"] = get_argv(argvs, argvs.index("-bgco"), result["bgco"])
    if "-trans-mode" in argvs:
        result["trans-mode"] = get_argv(argvs, argvs.index("-trans-mode"), result["trans-mode"])
    if "-beat-mode" in argvs:
        result["beat-mode"] = True
        if "-time" in argvs:
            result["time"] = get_argv(argvs, argvs.index("-time"), result["time"])
        if "-beat-rate" in argvs:
            result["beat-rate"] = get_argv(argvs, argvs.index("-beat-rate"), result["beat-rate"])
    return result
    
def get_recognize_commands(argvs, index, length):
    #default values
    result = {"mode":"fastest", "sample-rate":1, "slice-path":''}
    if index + 1 == length:
        log.log("get_recognize_commands", "not enough parameters")
        return None
    argvs = argvs[index + 1:]
    if "-slice-path" in argvs:
        result["slice-path"] = get_argv(argvs, argvs.index("-slice-path"), result["slice-path"])
    if "-mode" in argvs:
        result["mode"] = get_argv(argvs, argvs.index("-mode"), result["mode"])
    if "-sample-rate" in argvs:
        result["sample-rate"] = get_argv(argvs, argvs.index("-sample-rate"), result["sample-rate"])
    return result

def get_train_help_commands(argvs, index, length):
    #default values
    result = {"use-learn-pic":False, "max-pic-num":0, "use-slice":None}
    argvs = argvs[index + 1:]
    if "-use-learn-pic" in argvs:
        result["use-learn-pic"] = True
    if "-use-slice"in argvs:
        result["use-slice"] = get_argv(argvs, argvs.index("-use-slice"), result["use-slice"])
    if "-max-pic-num" in argvs:
        result["max-pic-num"] = get_argv(argvs, argvs.index("-max-pic-num"), result["max-pic-num"])
    return result

    
def execute_learn_commands(argvs):
    rescan = True if "-rescan" in argvs else False
    rec.learn_aragaki(rescan)
    exit()
    
def execute_recognize_commands(argvs):
    commands = get_recognize_commands(argvs, argvs.index("--recognize"), len(sys.argv))
    if commands == None:
        exit()
    rec.recognize_aragaki(commands)
    exit()
    
def execute_listen_commands(argvs):
    rescan = True if "-rescan" in argvs else False
    beat_detect_mode = "manual" if '-manual-beat' in argvs else "auto"
    mus.find_music(rescan, beat_detect_mode)
    exit()
    
def execute_train_commands(argvs):
    if "-train-help" in argvs:
        commands = get_train_help_commands(argvs, argvs.index("-train-help"), len(sys.argv))
        if commands == None:
            exit()
        recexp.help_marking(commands, rec.picture_path)
        exit()
    elif "-start" in argvs:
        recexp.training()
        exit()
        
def execute_album_learn_commands(argvs):
    folder = None
    if "-folder" in argvs:
        folder = get_argv(argvs, argvs.index("-folder"), "")
    rescan = True if "-rescan" in argvs else False
    alb.learn_picture(folder, rescan)
    exit()
    
def execute_slice_pocess_commands(argvs):
    result = {"feature":"", "express":"default", \
                "top-cut":0, "bottom-cut":0, "left-cut":0, "right-cut":0, "slow-times":0, \
                "slice-size-range":"0-255","slice-path":'',"scan":"info", "mode":"auto"}
    if '-slice-path' in argvs:
        result["slice-path"] = get_argvs(argvs, argvs.index("-slice-path"), result["slice-path"])
    if "-feature" in argvs:
        result["feature"] = get_argv(argvs, argvs.index("-feature"), result["feature"])
    if "-scan" in argvs:
        result["scan"] = get_argv(argvs, argvs.index("-scan"), result["scan"])
        if result["scan"] == "info":
            rec.sync_slice_info(result["slice-path"])
        elif result["scan"] == "face":
            rec.sync_slice_face_info(result["slice-path"])
        elif result["scan"] == "express":
            if "-mode" in argvs:
                result["mode"] = get_argv(argvs, argvs.index("-mode"), result["mode"])
            rescan = True if "-rescan" in argvs else False
            rec.sync_slice_express_info(result["slice-path"], result["mode"], result["feature"], rescan)
        exit()
    if "-slice-size-range" in argvs:
        result["slice-size-range"] = get_argv(argvs, argvs.index("-slice-size-range"), result["slice-size-range"])
    if "-express" in argvs:
        result["express"] = get_argv(argvs, argvs.index("-express"), result["express"])
    if "-cut-scene" in argvs:
        mov.cut_scene(result)
    elif "-get-slice-length" in argvs:
        express = get_argv(argvs, argvs.index("-get-slice-length"), "default")
        length = rec.get_movie_express_slices_length(express, result)
        log.log("get-slice-length", "express [%s] total length is %d seconds" %(express, length))
    elif "-slow-slice" in argvs:
        result["slow-times"] = get_argv(argvs, argvs.index("-slow-slice"), result["slow-times"])
        slice_list = mov.slomo_slice(result)
    elif "-cut-slice" in argvs:
        result["slice-size"] = get_argv(argvs, argvs.index("-slice-size"), result["slice-size"])
        mov.cut_slices(result)
    elif "-cut-size" in argvs:
        if "-top-cut" in argvs:
            result["top-cut"] = get_argv(argvs, argvs.index("-top-cut"), result["top-cut"])
        if "-bottom-cut" in argvs:
            result["bottom-cut"] = get_argv(argvs, argvs.index("-bottom-cut"), result["bottom-cut"])
        if "-left-cut" in argvs:
            result["left-cut"] = get_argv(argvs, argvs.index("-left-cut"), result["left-cut"])
        if "-right-cut" in argvs:
            result["right-cut"] = get_argv(argvs, argvs.index("-right-cut"), result["right-cut"])
        mov.cut_size(result)
    elif "-cut-face" in argvs:
        mov.cut_face(result)
    exit()
    
def execute_make_mv_commands(argvs):
    if "-random" in argvs:
        commands = get_make_mv_random_commands()
    else:
        commands = get_make_mv_commands(argvs, argvs.index("--make-mv"), len(sys.argv))
    if commands == None:
        exit()
    mov.make_aragaki_movie(commands)
    exit()
    
def execute_make_album_commands(argvs):
    if "-random" in argvs:
        commands = get_make_album_random_commands()
    else:
        commands = get_make_album_commands(argvs, argvs.index("--make-album"), len(sys.argv))
    if commands == None:
        exit()
    alb.make_aragaki_album(commands)
    exit()
    
def execute_test_commands(argvs):
    width = 1024
    height = 768
    if "-width" in argvs:
        width = get_argv(argvs, argvs.index("-width"), 1024)
    if "-height" in argvs:
        height = get_argv(argvs, argvs.index("-height"), 768)
    if "-test-oped" in argvs:
        file_name = get_argv(argvs, argvs.index("-test-oped"), None)
        if file_name == None:
            exit()
        painter = Painter("", log, Cfg)
        graph = painter.generate_image(file_name, width, height)
        if graph != []:
            show_image("test-oped", graph)
        exit()
    if "-test-lrc" in argvs:
        file_name = get_argv(argvs, argvs.index("-test-lrc"), None)
        if file_name == None:
            exit()
        painter = Painter("", log, Cfg)
        lrc_info = painter.get_lrc_json(file_name)
        if lrc_info == None:
            exit()
        lrc_origin = painter.get_lrc(lrc_info["id"])
        lrcs = lrc_origin["lyric"].split('\n')
        time_list = []
        lrc_list = []
        for lrc in lrcs:
            try:
                t = lrc[1:lrc.index(']')]
                m = int(t.split(':')[0])
                s = float(t.split(':')[1])
                time_list.append(m*60 + s)
                lrc_list.append(lrc[lrc.index(']')+1:])
            except Exception as e:
                continue
        for i in range(600, 630, 2):
            bg = np.ones((height, width, 3), dtype=np.uint8)
            #rgb type
            bg[:,:,:] = 0
            out = painter.paint_lrc(time_list, lrc_list, bg, i/30, (lrc_info["top"], lrc_info["left"]), lrc_info["color"], lrc_info["size"], lrc_info["font"])
            show_image("test-lrc", out)
        exit()
        
def execute_commands(argvs):
    #prepare
    if len(argvs) == 0 or "--help" in argvs:
        print_help()
        exit()
    if "--learn" in argvs:
        execute_learn_commands(argvs)
    if "--recognize" in argvs:
        execute_recognize_commands(argvs)
    if "--listen" in argvs:
        execute_listen_commands(argvs)
    if "--train-exp" in argvs:
        execute_train_commands(argvs)
    if "--album-learn" in argvs:
        execute_album_learn_commands(argvs)
    if "--slice-process" in argvs:
        execute_slice_pocess_commands(argvs)
    if '--test' in argvs:
        execute_test_commands(argvs)
    '''
    if "--catch" in argvs:
        catch_thing = get_argv(argvs, argvs.index("--catch"))
        if catch_thing == None:
            log.log("catch", "not enough parameters")
            exit()
        cat.catch_gaki(catch_thing)
        exit()
    '''
    #make-mv
    if "--make-mv" in sys.argv:
        execute_make_mv_commands(argvs)
        exit()
    if "--make-album" in sys.argv:
        execute_make_album_commands(argvs)
        exit()
    
    
    

if __name__ == "__main__":
    sys.argv.pop(0)
    execute_commands(sys.argv)