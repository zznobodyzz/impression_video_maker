import copy
from moviepy.editor import *
from moviepy.audio.fx import *
from utils import *
import cv2
from painter import OPED_Painter
from any2jpg import any2jpg
import numpy as np
import math

class Alb():
    def __init__(self, log, recexp, mus):
        self.log = log
        self.mus = mus
        self.recexp = recexp
        self.workarea = "./wa/"
        self.output_movie_path = self.workarea + "output_movie/"
        self.material_path = self.workarea + "material/"
        self.font_type_path = self.workarea + "material/font/"
        self.default_album_path = self.workarea + "album_of_gaki/"
        self.picture_database = self.workarea + "album_db.pkl"
        self.opening_seconds = 4
        self.ending_seconds = 3
        self.default_wdco = "[255,255,255]"
        self.default_bgco = "[0,0,0]"
        self.default_album_bg_co = tuple([255,255,255])
        self.default_enlarge_limit = 0.75
        self.pic_db = None
        self.painter = OPED_Painter(self.workarea, self.output_movie_path, self.material_path, \
                                    self.font_type_path, self.default_wdco, self.default_bgco, \
                                    self.opening_seconds, self.ending_seconds, self.log)
        self.trans_mode_list = ("random", "topin", "bottomin", "leftin", "rightin", "fade")
        
    def init_picture_database(self):
        if self.pic_db != None:
            return
        if os.path.exists(self.picture_database) == False:
            self.log.log("init_picture_database", "no pic_db found, use new db")
            self.pic_db = dict()
        else:
            self.pic_db = load_pkl(self.picture_database)
            if self.pic_db == None:
                self.log.log("init_picture_database", "pic_db is empty, use new db")
                self.pic_db = dict()
            else:
                self.log.log("init_picture_database", "found pic_db, going to use it")
                
    def save_picture_database(self):
        save_pkl(self.picture_database, self.pic_db)
    
    def convert_pic_type(self, file_path):
        if file_path.split(".")[-1] != "jpg":
            new_file_path = ".".join(file_path.split(".")[:-1]) + ".jpg"
            any2jpg(file_path, new_file_path)
            os.remove(file_path)
            self.log.log("convert_pic_type", "converted [%s] to [%s], [%s] has been deleted automatically" %(file_path, new_file_path, file_path))
            return new_file_path.split('/')[-1]
        else:
            return file_path.split('/')[-1]
    
    def learn_picture(self, folder, rescan):
        if folder == None:
            pic_folder = self.default_album_path
        else:
            pic_folder = self.workarea + folder + '/' if folder[-1] != '/' else ''
            if os.path.exists(pic_folder) == False:
                self.log.log("learn_picture", "specified folder not exists, use default folder")
                if os.path.exists(self.default_album_path) == False:
                    os.mkdir(self.default_album_path)
                    self.log.log("learn_picture", "folder %s not exists, created automatically, this may be your first time running this program, please try to find some pictures and put them into folder %s" %(self.default_album_path,self.default_album_path))
                    return
                pic_folder = self.default_album_path
        new_file = []
        self.init_picture_database()
        self.recexp.load_recognizer()
        if rescan == True:
            for pic in list(self.pic_db.keys()):
                if pic_folder == '/'.join(pic.split('/')[:-1]) + '/':
                    del self.pic_db[pic]
        for pic in os.listdir(pic_folder):
            pic_path = pic_folder + self.convert_pic_type(pic_folder + pic)
            if pic_path in self.pic_db.keys():
                continue
            frame = cv2.imread(pic_path)
            express = self.recexp.predict_image(frame)
            if express == None:
                express = "default"
                self.log.log("learn_picture", "treated as a default face")
            self.pic_db[pic_path] = dict()
            self.pic_db[pic_path]["height"] = frame.shape[0]
            self.pic_db[pic_path]["width"] = frame.shape[1]
            self.pic_db[pic_path]["express"] = express
            new_file.append(pic_path)
        if new_file != []:
            self.log.log("learn_picture", "successfully loaded %d pictures" %(len(new_file)))
            self.log.log("learn_picture", "they are [" + " ".join(new_file) + "]")
        self.save_picture_database()
            
    def get_music(self, song_name):
        if self.mus.mus_db == None:
            self.mus.init_music_database()
        if len(self.mus.mus_db.keys()) == 0:
            self.log.log("get_music", "you haven't load any music yet, please try --listen first")
            return None, None
        for music_file, info in self.mus.mus_db.items():
            if fuzzy_match_file_name(song_name, music_file):
                return self.mus.music_path + music_file, info
        self.log.log("get_music", "song %s not found" %(song_name))
        return None, None
        
    def get_pictures(self, commands):
        express_pictures = []
        for pic, info in self.pic_db.items():
            if info["express"] == commands["express"] or commands["express"] == "default":
                express_pictures.append(pic)
        if commands["allow-repeat"] == False and commands["pic-num"] > len(express_pictures):
            self.log.log("get_pictures", "there is not enough picture with express[%s] to make album, have [%d], specified [%d]" %(commands["express"], len(express_pictures), commands["pic-num"]))
            return None
        picked_pictures = []
        last_index = -1
        for i in range(commands["pic-num"]):
            index = get_random_i(0, len(express_pictures) - 1)
            if commands["allow-repeat"] == False:
                picked_pictures.append(express_pictures[index])
                express_pictures.pop(index)
            else:
                while index == last_index:
                    index = get_random_i(0, len(express_pictures) - 1)
                picked_pictures.append(express_pictures[index])
                last_index = index
        return picked_pictures
    
    def get_beats_by_rate(self, beats, rate):
        select_beats = []
        final = []
        step = len(beats)//rate
        if step == 0:
            step = 1
        for i in range(0, len(beats)+1, step):
            select_beats.append(beats[i])
        return select_beats
    
    def preprocess_music(self, commands, music_file_list, music_info_list):
        if commands["beat-mode"] == True:
            music_time = commands["time"]
            if music_time == 0:
                music_time = music_info_list[0]["duration"]
        else:
            music_time = commands["pic-num"] * commands["interval"]
        music = AudioFileClip(music_file_list[0])
        if int(music_info_list[0]["duration"]) >= music_time:
            music = music.subclip(0, music_time)
            origin_beats = self.get_beats_by_rate(music_info_list[0]["beats"], commands["beat-rate"])
            for j in range(len(origin_beats)):
                if origin_beats[j] > music_time:
                    break
            beats = []
            beats.extend(origin_beats[:j])
            if int(music_info_list[0]["duration"]) == music_time:
                beats.append(music_info_list[0]["duration"])
            music = audio_fadeout.audio_fadeout(music, 2)
            return music, beats
        music = audio_fadeout.audio_fadeout(music, 1)
        music_list = [copy.deepcopy(music)]
        beats = []
        origin_beats = self.get_beats_by_rate(music_info_list[0]["beats"], commands["beat-rate"])
        beats.extend(origin_beats)
        beats.append(music_info_list[0]["duration"])
        i = 1
        music_time -= music_info_list[0]["duration"]
        while music_time > 0:
            if len(music_file_list) == 1 or i == len(music_file_list):
                i = 0
            music = AudioFileClip(music_file_list[i])
            origin_beats = self.get_beats_by_rate(music_info_list[i]["beats"], commands["beat-rate"])
            music = audio_fadein.audio_fadein(music, 1)
            if music_info_list[i]["duration"] > music_time:
                music = music.subclip(0, music_time)
                music = audio_fadeout.audio_fadeout(music, 2)
                music_list.append(music)
                for j in range(origin_beats):
                    if origin_beats[j] > music_time:
                        break
                beats.extend(music_info_list[i]["beats"][:j])
                break
            else:
                music = audio_fadeout.audio_fadeout(music, 1)
                music_list.append(music)
                beats.extend(origin_beats)
                beats.append(music_info_list[i]["duration"])
            music_time - music_info_list[i]["duration"]
            i += 1
        return concatenate_audioclips(music_list), beats
        
    def generate_background(self, commands, picture_list):
        height_list = []
        for pic in picture_list:
            height_list.append(self.pic_db[pic]["height"])
        max_height = max(height_list)
        min_height = min(height_list)
        video_height = (max_height + min_height)//2
        #max 1920*1080
        if video_height > 1080:
            video_height = 1080
        video_width = video_height//9*16
        if commands["bggr"] != None:
            if os.path.exists(self.material_path + commands["bggr"]) == True:
                bg = cv2.imread(self.material_path + commands["bggr"])
                bg = bg.astype("uint16")
                bg = cv2.resize(bg, (video_width, video_height))
                return bg, video_width, video_height
            self.log.log("generate_background", "background file [%s] not found, use default background" %(commands["bggr"]))
        if commands["bgco"] != None:
            bg_rgb = self.painter.decode_color_string(commands["bgco"])
            if bg_rgb == None:
                self.log.log("generate_background", "rgb color format is not right, use default color")
                bg_rgb = self.default_album_bg_co
        bg = np.ones((video_height, video_width, 3), dtype=np.uint16)
        #bgr type
        bg[:,:,0] = bg_rgb[2]
        bg[:,:,1] = bg_rgb[1]
        bg[:,:,2] = bg_rgb[0]
        return bg, video_width, video_height
        
    def check_tilt_out_of_screen(self, ih, iw, vh, vw, angle):
        sin = math.sin(math.radians(angle))
        cos = math.cos(math.radians(angle))
        rh = math.ceil(ih * cos + iw * sin)
        rw = math.ceil(ih * sin + iw * cos)
        if rh > vh or rw > vw:
            return True, 0, 0
        return False, rh, rw
        
    def liner_set_value(self, image, height, width):
        for i in range(5, height - 5):
            start_index = 0
            end_index = width - 1
            for j in range(width):
                if (image[i][j] == [256,256,256]).all() == False:
                    start_index = j
                    break
            for j in range(width-1, -1, -1):
                if (image[i][j] == [256,256,256]).all() == False:
                    end_index = j
                    break
            start_index = 5 if start_index < 5 else start_index
            end_index = width - 5 if end_index > width - 5 else end_index
            for j in range(start_index, end_index):
                if (image[i][j] == [256,256,256]).all() == True:
                    h_a = image[i-5:i+5,j-5:j+5,:]
                    f = h_a.reshape(100,3)
                    f = f[f<256]
                    f = np.mean(f, axis=0)
                    image[i][j] = f.astype("uint16")
        return image
        
    def spin_picture(self, image, image_height, image_width, video_height, video_width):
        angle = get_random_i(5,15)
        angle_direction = get_random_s(["clock", "conterclock"])
        final_height = 0
        final_width = 0
        while True:
            ret, final_height, final_width = self.check_tilt_out_of_screen(image_height, image_width, video_height, video_width, angle)
            if ret == False:
                break
            angle -= 3
            if angle < 5:
                return image
        if angle_direction == "conterclock":
            angle = 360 - angle
        Matrix = cv2.getRotationMatrix2D((image_width/2, image_height/2), angle, 1.0)
        center_w = image_width/2
        center_w_delta = center_w + (final_width - image_width) / 2
        center_h = image_height/2
        center_h_delta = center_h + (final_height - image_height) / 2
        bg = np.ones((final_height, final_width, 3), dtype=np.uint16)
        cos = math.cos(math.radians(angle))
        sin = math.sin(math.radians(angle))
        bg[:,:,:] = 256
        for i in range(image_height):
            for j in range(image_width):
                x = int((j-center_w)*cos-(i-center_h)*sin+center_w_delta)
                y = int((j-center_w)*sin+(i-center_h)*cos+center_h_delta)
                bg[y][x] = image[i][j]
        bg = self.liner_set_value(bg, final_height, final_width)
        return bg
        
    def cover_picture(self, bg, image, video_height, video_width, image_height, image_width, h_delta, w_delta):
        i=0
        j=0
        start_cover_pos_h = math.ceil((video_height - image_height)/2) + h_delta
        end_cover_pos_h = start_cover_pos_h + image.shape[0]
        start_cover_pos_w = math.ceil((video_width - image_width)/2) + w_delta
        end_cover_pos_w = start_cover_pos_w + image.shape[1]
        for h in range(start_cover_pos_h, end_cover_pos_h):
            if h >= 0 and h < video_height:
                j = 0
                for w in range(start_cover_pos_w, end_cover_pos_w):
                    if w >= 0 and w < video_width and (image[i][j] == [256,256,256]).any() == False:
                        bg[h][w] = image[i][j]
                    j+=1
            i+=1
        return bg

    def generate_album_picture(self, pic, bg, video_height, video_width):
        image = cv2.imread(pic)
        image = image.astype("uint16")
        image_height = image.shape[0]
        image_width = image.shape[1]
        if image_height < video_height * self.default_enlarge_limit:
            enlarge_sample = video_height * self.default_enlarge_limit / image_height
            image_width = int(enlarge_sample*image_width)
            image_height = int(enlarge_sample*image_height)
            image = cv2.resize(image, (image_width, image_height))
            image = self.spin_picture(image, image_height, image_width, video_height, video_width)
        elif image_height > video_height:
            image_width = int(video_height/image.shape[0]*image.shape[1])
            image = cv2.resize(image, (image_width, video_height))
        if image_width > video_width:
            image = image[:,(image_width - video_width)//2:image_width - start_cut_pos,:]
        image_height = image.shape[0]
        image_width = image.shape[1]
        bg = self.cover_picture(bg, image, video_height, video_width, image_height, image_width, 0, 0)
        bg_tmp = bg.astype("uint8")
        return bg, image
    
    def fade_out_picture(self, image, pic_nums, current_times, height_slice_nums, width_slice_nums):
        image_height = image.shape[0] - image.shape[0]%height_slice_nums
        image_width = image.shape[1] - image.shape[1]%width_slice_nums
        height_step = image_height//height_slice_nums
        width_step = image_width//width_slice_nums
        for i in range(0, image_height, height_step):
            for j in range(0, image_width, width_step):
                for k in range(0, height_step//pic_nums*current_times):
                    for l in range(0, width_step//pic_nums*current_times):
                        image[i+k][j+l] = [256,256,256]
        height_step_2 = 1 if (image.shape[0] - image_height) < height_slice_nums else (image.shape[0] - image_height)//height_slice_nums
        for i in range(0, image_width, width_step):
            for m in range(image_height, image.shape[0], height_step_2):
                for n in range(0, width_step//pic_nums*current_times):
                    image[m][n+i] = [256,256,256]
        for m in range(image_height, image.shape[0], height_step_2):
            for r in range(image_width, image.shape[1]):
                image[m][r] = [256,256,256]
        width_step_2 = 1 if (image.shape[1] - image_height) < height_slice_nums else (image.shape[1] - image_height)//height_slice_nums
        for j in range(0, image_height, height_step):
            for o in range(image_width, image.shape[1], width_step_2):
                for p in range(0, height_step//pic_nums*current_times):
                    image[p+j][o] = [256,256,256]
        return image
        
    def fade_in_picture(self, bg, image, pic_nums, current_times, height_slice_nums, width_slice_nums):
        image_height = bg.shape[0] - bg.shape[0]%height_slice_nums
        image_width = bg.shape[1] - bg.shape[1]%width_slice_nums
        height_step = image_height//height_slice_nums
        width_step = image_width//width_slice_nums
        for i in range(0, image_height, height_step):
            for j in range(0, image_width, width_step):
                for k in range(0, height_step//pic_nums*current_times):
                    for l in range(0, width_step//pic_nums*current_times):
                        bg[i+k][j+l] = image[i+k][j+l]
        height_step_2 = 1 if (bg.shape[0] - image_height) < height_slice_nums else (bg.shape[0] - image_height)//height_slice_nums
        for i in range(0, image_width, width_step):
            for m in range(image_height, bg.shape[0], height_step_2):
                for n in range(0, width_step//pic_nums*current_times):
                    bg[m][n+i] = image[m][n+i]
                for r in range(image_width, bg.shape[1]):
                    bg[m][r] = image[m][r]
        width_step_2 = 1 if (bg.shape[1] - image_height) < height_slice_nums else (bg.shape[1] - image_height)//height_slice_nums
        for j in range(0, image_height, height_step):
            for o in range(image_width, bg.shape[1], width_step_2):
                for p in range(0, height_step//pic_nums*current_times):
                    bg[p+j][o] = image[p+j][o]
        return bg
    
    def generate_album_anime(self, bg_base, first_pic, second_pic, pic_nums, trans_mode):
        video_height = bg_base.shape[0]
        video_width = bg_base.shape[1]
        first_pic_height = first_pic.shape[0]
        first_pic_width = first_pic.shape[1]
        second_pic_height = second_pic.shape[0]
        second_pic_width = second_pic.shape[1]
        anime = []
        if trans_mode not in self.trans_mode_list:
            trans_mode = "fade"
        if trans_mode == "random":
            trans_mode = self.trans_mode_list[get_random_i(1, len(self.trans_mode_list) - 1)]
        if trans_mode == "fade":
            fade_pic_nums = math.ceil(pic_nums/2)
            for i in range(fade_pic_nums - 1):
                #first handle first pic disappear
                bg = copy.deepcopy(bg_base)
                #default set 8 * 8 squals
                first_pic = self.fade_out_picture(first_pic, fade_pic_nums - 1, i, 8, 8)
                anime.append(copy.deepcopy(self.cover_picture(bg, first_pic, video_height, video_width, first_pic_height, first_pic_width, 0, 0)))
            first_empty_image = np.ones((first_pic_height, first_pic_width, 3), dtype=np.uint16)
            first_empty_image[:,:,:] = 256
            anime.append(copy.deepcopy(self.cover_picture(bg, first_empty_image, video_height, video_width, first_pic_height, first_pic_width, 0, 0)))
            second_empty_image = np.ones((second_pic_height, second_pic_width, 3), dtype=np.uint16)
            second_empty_image[:,:,:] = 256
            for i in range(fade_pic_nums - 1):
                #then handle second pic show
                bg = copy.deepcopy(bg_base)
                second_empty_image = self.fade_in_picture(second_empty_image, second_pic, fade_pic_nums - 1, i, 8, 8)
                anime.append(copy.deepcopy(self.cover_picture(bg, second_empty_image, video_height, video_width, second_pic_height, second_pic_width, 0, 0)))
            anime.append(copy.deepcopy(self.cover_picture(bg, second_pic, video_height, video_width, second_pic_height, second_pic_width, 0, 0)))
            return anime
        step = video_width//pic_nums
        if trans_mode == "topin":
            delta_h_out_range = range(0, video_height, step)
            delta_w_out_range = [0]
            delta_h_in_range = range(-video_height, 0, step)
            delta_w_in_range = [0]
        elif trans_mode == "bottomin":
            delta_h_out_range = range(0, -video_height, -step)
            delta_w_out_range = [0]
            delta_h_in_range = range(video_height, 0, -step)
            delta_w_in_range = [0]
        elif trans_mode == "leftin":
            delta_h_out_range = [0]
            delta_w_out_range = range(0, video_width, step)
            delta_h_in_range = [0]
            delta_w_in_range = range(-video_width, 0, step)
        elif trans_mode == "rightin":
            delta_h_out_range = [0]
            delta_w_out_range = range(0, -video_width, -step)
            delta_h_in_range = [0]
            delta_w_in_range = range(video_width, 0, -step)
        #first process first pic move out to the bottom
        for delta_h in delta_h_out_range:
            for delta_w in delta_w_out_range:
                bg = copy.deepcopy(bg_base)
                anime.append(copy.deepcopy(self.cover_picture(bg, first_pic, video_height, video_width, first_pic_height, first_pic_width, delta_h, delta_w)))
        #then process second pic move in from the top
        index = 0
        for delta_h in delta_h_in_range:
            for delta_w in delta_w_in_range:
                anime[index] = self.cover_picture(anime[index], second_pic, video_height, video_width, second_pic_height, second_pic_width, delta_h, delta_w)
                index += 1
        return anime
        
    def combine_pictures_by_interval(self, commands, output_file_name, picture_list):
        self.log.log("combine_pictures_by_interval", "generating background graph")
        bg, video_width, video_height = self.generate_background(commands, picture_list)
        fourcc = cv2.VideoWriter_fourcc('h', '2', '6', '4')
        output_flow = cv2.VideoWriter(output_file_name, cv2.VideoWriter_fourcc('h', '2', '6', '4'), 30, (video_width,video_height))
        bg_base = copy.deepcopy(bg)
        bg_list = []
        image_list = []
        self.log.log("combine_pictures_by_interval", "generating album base graph")
        for pic in picture_list:
            bg, image = self.generate_album_picture(pic, bg, video_height, video_width)
            bg_list.append(bg)
            image_list.append(image)
            bg = copy.deepcopy(bg_base)
        self.log.log("combine_pictures_by_interval", "generating video file and graph-change-anime")
        for index in range(len(bg_list)):
            anime = []
            anime_nums = 0
            if index != len(picture_list) - 1:
                anime_nums = 6 * commands["interval"]
                anime = self.generate_album_anime(bg_base, image_list[index], image_list[index+1], anime_nums, commands["trans-mode"])
            for i in range(30 * commands["interval"] - anime_nums):
                bg_list[index] = bg_list[index].astype("uint8")
                output_flow.write(bg_list[index])
            for i in range(1, anime_nums+1):
                anime_index = round((len(anime)-1)/anime_nums*i)
                anime[anime_index] = anime[anime_index].astype("uint8")
                output_flow.write(anime[anime_index])
            self.log.log("combine_pictures_by_interval", "schedule: %d%%" %(index*100//len(bg_list)))
        output_flow.release()
        return 30, video_width, video_height, 'h264', fourcc
        
    def combine_pictures_by_beats(self, commands, output_file_name, picture_list, beats):
        bg, video_width, video_height = self.generate_background(commands, picture_list)
        fourcc = cv2.VideoWriter_fourcc('h', '2', '6', '4')
        output_flow = cv2.VideoWriter(output_file_name, cv2.VideoWriter_fourcc('h', '2', '6', '4'), 30, (video_width,video_height))
        bg_base = copy.deepcopy(bg)
        i = 0
        last_beat = 0
        max_frames = commands["time"] * 30
        current_frames = 0
        time_up = False
        for beat in beats:
            bg = self.generate_album_picture(picture_list[i], bg, video_height, video_width)
            for j in range(int(30 * (beat - last_beat))):
                output_flow.write(bg)
                current_frames += 1
                if current_frames == max_frames:
                    time_up = True
            if time_up == True:
                break
            bg = copy.deepcopy(bg_base)
            i += 1
            if i == len(picture_list):
                i = 0
        output_flow.release()
        return 30, video_width, video_height, 'h264', fourcc
        
    def add_music(self, music_clip, music_file, movie_file, final_file, codec):
        music_official_name = music_file.split('/')[-1]
        music_official_name = '.'.join(music_official_name.split('.')[:-1])
        final_file += '_' + music_official_name + '.avi'
        movie = VideoFileClip(movie_file)
        final = movie.set_audio(music_clip).fadeout(2, (1, 1, 1))
        final = final.fadein(1, (1, 1, 1))
        final.write_videofile(final_file, codec = codec)
        return final, final_file
        
    def make(self, commands, music_file_list, music_info_list, picture_list):
        music_clip, beats = self.preprocess_music(commands, music_file_list, music_info_list)
        movie_file = self.output_movie_path + commands["title"] + '.avi'
        if commands["beat-mode"] == True:
            fps, width, height, codec_str, codec = self.combine_pictures_by_beats(commands, movie_file, picture_list, beats)
        else:
            fps, width, height, codec_str, codec = self.combine_pictures_by_interval(commands, movie_file, picture_list)
        out_movie, out_movie_path = self.add_music(music_clip, music_file_list[0], movie_file, self.output_movie_path + commands["title"], codec_str)
        if commands["opwd"] == None and commands["opgr"] == None \
            and commands["edwd"] == None and commands["edgr"] == None:
            os.remove(movie_file)
            return
        full_movie = []
        make_opening = False
        make_ending = False
        if commands["opwd"] != None or commands["opgr"] != None:
            make_opening = True
            image = self.painter.generate_image(commands["opconf"], width, height)
            if image == []:
                return
            opening_movie, opening_file_name = self.painter.add_opening_or_ending("opening", out_movie_path, image, fps, codec, width, height)
            full_movie.append(opening_movie)
        full_movie.append(out_movie)
        if commands["edwd"] != None or commands["edgr"] != None:
            make_ending = True
            image = self.painter.generate_image(commands["edconf"], width, height)
            if image == []:
                return
            ending_movie, ending_file_name = self.painter.add_opening_or_ending("ending", out_movie_path, image, fps, codec, width, height)
            full_movie.append(ending_movie)
        final_movie = concatenate_videoclips(full_movie, method='compose')
        final_path = '.'.join(out_movie_path.split('.')[:-1]) + \
                        ('_op' if make_opening == True else '') + \
                        ('_ed' if make_ending == True else '') + \
                        '.' + out_movie_path.split('.')[-1]
        final_movie.write_videofile(final_path, codec = codec_str)
        if make_opening == True:
            os.remove(opening_file_name)
        if make_ending == True:
            os.remove(ending_file_name)
        os.remove(movie_file)
        os.remove(out_movie_path)
        
    def make_aragaki_album(self, commands):
        self.init_picture_database()
        music_file_list = []
        music_info_list = []
        for music_name in commands["music"]:
            music_file, music_info = self.get_music(commands["music"])
            if music_file == None:
                return
            music_file_list.append(music_file)
            music_info_list.append(music_info)
        self.log.log("make_aragaki_album", "%d songs are loaded, they are [" %(len(music_file_list)) + ' '.join(music_file_list) + ']')
        picture_list = self.get_pictures(commands)
        self.log.log("make_aragaki_album", "%d pictures are loaded, they are [" %(len(picture_list)) + ' '.join(picture_list) + ']')
        output_movie = self.make(commands, music_file_list, music_info_list, picture_list)
        
        