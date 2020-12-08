import copy
from moviepy.editor import *
from moviepy.audio.fx import *
import moviepy.config as moviepy_config
from utils import *
import cv2
import numpy as np
from painter import Painter
import math
import collections

class Mov():
    def __init__(self, log, rec, mus, cfg):
        self.log = log
        self.rec = rec
        self.mus = mus
        self.workarea = cfg.get_cfg("main", "workarea")
        self.output_movie_path = self.workarea + cfg.get_cfg("movie", "output_movie_path")
        self.default_output_fourcc = cfg.get_cfg("movie", "default_output_fourcc")
        self.default_moviepy_codec = cfg.get_cfg("movie", "default_moviepy_codec")
        self.default_output_suffix = cfg.get_cfg("movie", "default_output_suffix")
        self.default_output_fps = cfg.get_cfg("movie", "default_output_fps")
        self.face_effect_list = cfg.get_cfg("movie", "face_effect_list")
        self.convert_effect_list = cfg.get_cfg("movie", "convert_effect_list")
        self.screen_effect_list = cfg.get_cfg("movie", "screen_effect_list")
        self.painter = Painter(self.output_movie_path, log, cfg)
        self.ffmpeg_exe = cfg.get_cfg("main", "ffmpeg_path") + "ffmpeg.exe"
        if os.path.exists(self.ffmpeg_exe) == False:
            from imageio.plugins.ffmpeg import get_exe
            self.ffmpeg_exe = get_exe()
        else:
            moviepy_config.change_settings({"FFMPEG_BINARY":self.ffmpeg_exe})
        self.log.log("Mov init", "will use ffmpeg: %s" %(self.ffmpeg_exe))
        self.face_effect = "None"
        self.screen_effect = "None"
        self.convert_effect = "None"
        self.combine_mode = "follow"
        self.all_mode = False
        self.no_repeat = True
        
    def get_music(self, song_names):
        selected_music_file = []
        selected_music_info = []
        if self.mus.mus_db == None:
            self.mus.init_music_database()
        if len(self.mus.mus_db.keys()) == 0:
            self.log.log("get_music", "you haven't load any music yet, please try --listen first")
            return [], [], 0
        total_length = 0
        for song_name in song_names:
            found = False
            for music_file, info in self.mus.mus_db.items():
                if fuzzy_match_file_name(song_name, music_file):
                    selected_music_file.append(self.mus.music_path + music_file)
                    selected_music_info.append(info)
                    total_length += info["duration"]
                    found = True
                    break
            if found == False:
                self.log.log("get_music", "song %s not found" %(song_name))
                return [], [], 0
        return selected_music_file, selected_music_info, total_length
        
    def pick_slice(self, commands, min_size, max_size):
        if self.rec.slice_db == None:
            self.rec.init_slice_database(commands['slice-path'])
        express_slices = []
        for slice, slice_info in self.rec.slice_db[self.rec.slice_path].items():
            if (slice_info["express"] == commands["express"] or commands["express"] == "default") and \
                (commands["feature"] == "" or commands["feature"] in slice) and \
                (slice_info["length"] >= min_size * slice_info["fps"]) and \
                (slice_info["length"] <= max_size * slice_info["fps"]):
                    express_slices.append([slice, slice_info])
        if express_slices == []:
            self.log.log("pick_slice", "no slices were picked")
        return express_slices
        
    def get_slice(self, slices_list, frame_nums, slice_size, already_choosen):
        if self.all_mode == True:
            for express_slice in slices_list:
                if express_slice[0] not in already_choosen:
                    return express_slice
        index = get_random_i(0, len(slices_list) - 1)
        if self.no_repeat == True:
            while slices_list[index][0] in already_choosen or \
                slice_size > slices_list[index][1]["length"]/slices_list[index][1]["fps"] or \
                frame_nums > slices_list[index][1]["length"]:
                index = get_random_i(0, len(slices_list) - 1)
            return slices_list[index][0], slices_list[index][1]
        #make sure same slice won't be neighbour
        loop = 0
        while (slices_list[index][0] in already_choosen or \
                already_choosen[-1] == slices_list[index][0] or \
                frame_nums > slices_list[index][1]["length"] or \
                slice_size > slices_list[index][1]["length"]/slices_list[index][1]["fps"]) and \
                (loop < len(slices_list)):
            index = get_random_i(0, len(slices_list) - 1)
            loop += 1
        return slices_list[index][0], slices_list[index][1]
        
    def get_beats_by_rate(self, beats, rate):
        select_beats = []
        for i in range(0, len(beats), rate):
            select_beats.append(beats[i])
        return select_beats
        
    def write_frame_to_flow(self, flow, frame):
        flow.write(frame)
        
    def calc_compensation(self, beats, fps, precise):
        compensation = [0] * len(beats)
        payback = 0
        for i in range(len(beats) - 1):
            base1 = fps * (beats[i+1] - beats[i])
            base2 = int(base1)
            payback += (base1 - base2)
        if payback != 0:
            paybackf = round((len(beats) - 1)/payback, precise)
            i = 0
            while i < (len(beats) - 1):
                index = round(i * paybackf)
                if index > len(beats) - 1:
                    break
                compensation[index] += 1
                i += 1
        return compensation
        
    def combine_beats(self, beats, base_delta, least_beat_seconds):
        zip_times = 1
        if base_delta < 1:
            for i in [2,4,8,16,32,64]:
                if i * base_delta > least_beat_seconds:
                    zip_times = i
                    break
            i = 1
            length = len(beats) - 1
            while i < length:
                if beats[i+1] - beats[i] < least_beat_seconds:
                    for j in range(zip_times-1):
                        try:
                            beats.pop(i)
                        except Exception as e:
                            break
                    i += 1
                    length = len(beats) - 1
        return beats, base_delta*zip_times
        
    def follow_face_cut(self, frame, left, right, last_start_width, slice_width, last_pos, step):
        if left == 0 and right == 0:
            if step == 0:
                return -1
            start_width = last_start_width
        else:
            #if first frame of a flow
            if step == 0:
                if right - left > slice_width:
                    start_width = left + ((right - left - slice_width) // 2)
                else:
                    left_append_width = (slice_width - (right - left))//2
                    start_width = left - left_append_width
                    start_width = start_width if start_width > 0 else 0
            else:
                if abs(last_pos[0] - left) <= 20 and abs(last_pos[1] - right) <= 20:
                    start_width = last_start_width
                elif right - left > slice_width:
                    start_width = last_start_width
                elif left < last_start_width:
                    start_width = left
                    if abs(start_width - last_start_width) > 7:
                        start_width = last_start_width - 7
                elif right > (last_start_width + slice_width):
                    start_width = right - slice_width
                    if abs(start_width - last_start_width) > 7:
                        start_width = last_start_width + 7
                else:
                    start_width = last_start_width
        if start_width + slice_width > frame.shape[1]:
            start_width = frame.shape[1] - slice_width
        return start_width
        
    def nofollow_face_cut(self, frame, left, right, last_start_width, slice_width, last_pos):
        if left == 0 and right == 0:
            if last_pos[0] == 0 and last_pos[1] == 0:
                return -1
            else:
                start_width = last_start_width
        else:
            #if first frame of a flow
            if last_pos[0] == 0 and last_pos[1] == 0:
                if right - left > slice_width:
                    start_width = left + ((right - left - slice_width) // 2)
                else:
                    left_append_width = (slice_width - (right - left))//2
                    start_width = left - left_append_width
                    start_width = start_width if start_width > 0 else 0
                    if start_width + slice_width > frame.shape[1]:
                        start_width = frame.shape[1] - slice_width
            else:
                if abs(last_pos[0] - left) <= (last_pos[1] - last_pos[0])//2 and abs(last_pos[1] - right) <= (last_pos[1] - last_pos[0])//2:
                    start_width = last_start_width
                elif right - left > slice_width:
                    start_width = last_start_width
                elif left < last_start_width:
                    return -1
                elif right > (last_start_width + slice_width):
                    return -1
                else:
                    start_width = last_start_width
        return start_width
    
    def slice_flow_go_back(self, slice_flow_list, slice_flow_back_list):
        for i in range(len(slice_flow_list)):
            if slice_flow_back_list[i] != 0:
                current_pos = slice_flow_list[i].get(cv2.CAP_PROP_POS_FRAMES)
                slice_flow_list[i].set(cv2.CAP_PROP_POS_FRAMES, current_pos - slice_flow_back_list[i])
    
    def cross_screen_process(self, slice_flow_list, slice_info_list, last_start_width_list, last_pos_list, caption_height, step, video_size, beat_frame_nums):
        frame_list = []
        slice_width_list = [video_size[0]//len(slice_flow_list)]*len(slice_flow_list)
        slice_width_list[-1] += video_size[0]%len(slice_flow_list)
        slice_flow_back_list = [0] * len(slice_flow_list)
        for i in range(len(slice_flow_list)):
            slice_flow = slice_flow_list[i]
            slice_width = slice_width_list[i]
            slice_info = slice_info_list[i]
            last_start_width = last_start_width_list[i]
            last_pos = last_pos_list[i]
            if slice_info["fps"] >= self.default_output_fps * 1.5:
                ret, frame = slice_flow.read()
                if ret == False:
                    self.slice_flow_go_back(slice_flow_list, slice_flow_back_list)
                    return [], i
                slice_flow_back_list[i] += 1
            ret, frame = slice_flow.read()
            if ret == False:
                self.slice_flow_go_back(slice_flow_list, slice_flow_back_list)
                return [], i
            slice_flow_back_list[i] += 1
            if caption_height != 0:
                frame = frame[:int(frame.shape[0] * (1 - caption_height/100)),:,:]
            frame = cv2.resize(frame, video_size)
            if self.combine_mode == "follow":
                left, right, _ = self.rec.detect_face_info(frame, slice_info["width"], 0.1)
                #follow face mode
                start_width = self.follow_face_cut(frame, left, right, last_start_width, slice_width, last_pos, step)
                if start_width == -1:
                    self.slice_flow_go_back(slice_flow_list, slice_flow_back_list)
                    return [], i
                last_start_width_list[i] = start_width
                last_pos_list[i] = (left, right)
            else:
                if step % (self.default_output_fps * 2) == 0:
                    left, right, _ = self.rec.detect_face_info(frame, slice_info["width"], 0.1)
                    start_width = self.nofollow_face_cut(frame, left, right, last_start_width, slice_width, last_pos)
                    if start_width == -1:
                        self.slice_flow_go_back(slice_flow_list, slice_flow_back_list)
                        return [], i
                    last_pos_list[i] = (left, right)
                else:
                    start_width = last_start_width
                last_start_width_list[i] = start_width
            frame = frame[:,start_width:start_width+slice_width,:]
            if self.face_effect == "ghost":
                frame = self.painter.paint_ghost(step, beat_frame_nums, frame, self.default_output_fps)
            elif self.convert_effect == "vlog":
                frame = self.painter.vlog_convert(step, beat_frame_nums, frame, self.default_output_fps)
            frame_list.append(frame)
        for i in range(1, len(frame_list)):
            frame_list[0] = np.append(frame_list[0], frame_list[i], axis=1)
        return frame_list[0], 0
        
    def broadcast_screen_process(self, slice_flow_list, slice_info_list, caption_height, step, video_size, beat_frame_nums):
        frame_list = []
        width_nums = len(slice_flow_list)//6
        height_nums = len(slice_flow_list)//width_nums
        slice_width_list = [video_size[0]//width_nums]*width_nums
        slice_width_list[-1] += video_size[0]%width_nums
        slice_height_list = [video_size[1]//height_nums]*height_nums
        slice_height_list[-1] += video_size[1]%height_nums
        i = 0
        slice_flow_back_list = [0] * len(slice_flow_list)
        for h in range(len(slice_height_list)):
            for w in range(len(slice_width_list)):
                slice_width = slice_width_list[w]
                slice_height = slice_height_list[h]
                slice_flow = slice_flow_list[i]
                slice_info = slice_info_list[i]
                if slice_info["fps"] >= self.default_output_fps * 1.5:
                    ret, frame = slice_flow.read()
                    if ret == False:
                        self.slice_flow_go_back(slice_flow_list, slice_flow_back_list)
                        return [], i
                    slice_flow_back_list[i] += 1
                ret, frame = slice_flow.read()
                if ret == False:
                    self.slice_flow_go_back(slice_flow_list, slice_flow_back_list)
                    return [], i
                slice_flow_back_list[i] += 1
                if caption_height != 0:
                    frame = frame[:int(frame.shape[0] * (1 - caption_height/100)),:,:]
                frame = cv2.resize(frame, (slice_width, slice_height))
                if self.face_effect == "ghost":
                    frame = self.painter.paint_ghost(step, beat_frame_nums, frame, self.default_output_fps)
                elif self.convert_effect == "vlog":
                    frame = self.painter.vlog_convert(step, beat_frame_nums, frame, self.default_output_fps)
                frame_list.append(frame)
                i += 1
        hframe = []
        for h in range(len(slice_height_list)):
            wframe = frame_list[h*len(slice_width_list)]
            for w in range(1, len(slice_width_list)):
                wframe = np.append(wframe, frame_list[h*len(slice_width_list)+w], axis=1)
            hframe.append(wframe)
        frame = hframe[0]
        for i in range(1, len(hframe)):
            frame = np.append(frame, hframe[i], axis=0)
        return frame, 0
        
    def generate_frame(self, beat_frame_nums, slice_flow_list, slice_info_list, last_start_width_list, last_pos_list, caption_height, step, video_size):
        if len(slice_flow_list) == 1:
            slice_flow = slice_flow_list[0]
            slice_info = slice_info_list[0]
            if slice_info["fps"] >= self.default_output_fps * 1.5:
                ret, frame = slice_flow.read()
                if ret == False:
                    return [], 0
            ret, frame = slice_flow.read()
            if ret == False:
                return [], 0
            if caption_height != 0:
                frame = frame[:int(frame.shape[0] * (1 - caption_height/100)),:,:]
            frame = cv2.resize(frame, video_size)
            if self.face_effect == "ghost":
                frame = self.painter.paint_ghost(step, beat_frame_nums, frame, self.default_output_fps)
            elif self.convert_effect == "vlog":
                frame = self.painter.vlog_convert(step, beat_frame_nums, frame, self.default_output_fps)
            return frame, 0
        else:
            if len(slice_flow_list) <= 4:
                frame, failed_index = self.cross_screen_process(slice_flow_list, slice_info_list, last_start_width_list, last_pos_list, caption_height, step, video_size, beat_frame_nums)
            else:
                frame, failed_index = self.broadcast_screen_process(slice_flow_list, slice_info_list, caption_height, step, video_size, beat_frame_nums)
            return frame, failed_index
    
    def normalize_fps(self, slice_name):
        self.log.log("normalize_fps", "converting fps")
        clip = VideoFileClip(slice_name)
        tmp_file = append_file_name(slice_name, "_fps_conv")
        clip.write_videofile(tmp_file, fps=self.default_output_fps, codec = "libx264", logger = None)
        clip.close()
        return tmp_file
    
    def preprocess_slice_flow(self, slice_name, slice_info):
        if slice_info["fps"] != self.default_output_fps:
            tmp_file = self.normalize_fps(slice_name)
            slice_flow = cv2.VideoCapture(tmp_file)
            slice_info["fps"] = self.default_output_fps
            slice_info["length"] = int(slice_flow.get(cv2.CAP_PROP_FRAME_COUNT))
            slice_info["fourcc"] == int(slice_flow.get(cv2.CAP_PROP_FOURCC))
        else:
            tmp_file = None
            slice_flow = cv2.VideoCapture(slice_name)
        return tmp_file, slice_flow
    
    def prepare_beat_slice_flow(self, slices_list, beat_frame_nums, beat_time, output_size, already_choosen, is_failed):
        if len(slices_list) == 1:
            flow_list = []
            info_list = []
            tmp_file_list = []
            if self.screen_effect == "broadcast" and is_failed == False:
                pick_num = 48
            else:
                pick_num = 1
            for i in range(pick_num):
                slice_name, slice_info = self.get_slice(slices_list[0], beat_frame_nums, beat_time, already_choosen)
                tmp_file, slice_flow = self.preprocess_slice_flow(slice_name, slice_info)
                tmp_file_list.append(tmp_file)
                already_choosen.append(slice_name)
                flow_list.append(slice_flow)
                info_list.append(slice_info)
            return flow_list, info_list, tmp_file_list
        else:
            flow_list = []
            info_list = []
            tmp_file_list = []
            for slices in slices_list:
                slice_name, slice_info = self.get_slice(slices, beat_frame_nums, beat_time, already_choosen)
                tmp_file, slice_flow = self.preprocess_slice_flow(slice_name, slice_info)
                tmp_file_list.append(tmp_file)
                already_choosen.append(slice_name)
                flow_list.append(slice_flow)
                info_list.append(slice_info)
            return flow_list, info_list, tmp_file_list
    
    def prepare_no_beat_slice_flow(self, slices_list, already_choosen):
        flow_list = []
        info_list = []
        tmp_file_list = []
        for slices in slices_list:
            slice_name, slice_info = self.get_slice(slices, 0, 0, already_choosen)
            tmp_file, slice_flow = self.preprocess_slice_flow(slice_name, slice_info)
            tmp_file_list.append(tmp_file)
            already_choosen.append(slice_name)
            flow_list.append(slice_flow)
            info_list.append(slice_info)
        return flow_list, info_list
        
    def release_slices(self, slice_flow_list, tmp_file_list = []):
        for slice_flow in slice_flow_list:
            if slice_flow != None:
                slice_flow.release()
        for i in range(len(tmp_file_list)):
            if tmp_file_list[i] != None:
                os.remove(tmp_file_list[i])
                tmp_file_list[i] = None
        
    def get_movie_slice_base_info(self, slices_list):
        min_pixel = 3440*1440
        return_info = None
        for slice_list in slices_list:
            for slices in slice_list:
                current_pixel = slices[1]["width"] * slices[1]["height"]
                if current_pixel < min_pixel:
                    min_pixel = current_pixel
                    return_info = slices[1]
        return return_info
        
    def get_movie_slice_base_size(self, slices_list):
        statistics1 = list()
        statistics2 = list()
        for slice_list in slices_list:
            for slices in slice_list:
                key = [slices[1]["width"], slices[1]["height"]]
                if key not in statistics1:
                    statistics1.append(key)
                    statistics2.append(1)
                else:
                    statistics2[statistics1.index(key)] += 1
        return statistics1[statistics2.index(max(statistics2))]
        
    def check_fps_diff(self, slices_list):
        fps = None
        for slice_list in slices_list:
            for slices in slice_list:
                if fps != None and fps != slices[1]["fps"]:
                    return True
                fps = slices[1]["fps"]
        return False
        
    def combine_slices_with_beats(self, beats, slices_list, output_file_name, time, caption_height):
        already_choosen = []
        base_slice_info = self.get_movie_slice_base_info(slices_list)
        #real_height = int(base_slice_info["height"] * (1 - caption_height/100))
        base_slice_info["width"] = 3440
        real_height = 1440
        writed_frames = 0
        #don't know why but necessary
        for i in range(len(beats)):
            beats[i] -= 0.3
        beats[0] = 0
        combined_slice = collections.OrderedDict()
        output_flow = cv2.VideoWriter(output_file_name, self.default_output_fourcc, self.default_output_fps, (base_slice_info["width"],real_height))
        try:
            time_up = False
            total_length = self.default_output_fps * time
            need_write_ahead = False
            compensation = self.calc_compensation(beats, self.default_output_fps, 5)
            slice_list_ori = slices_list.copy()
            slice_list_all = []
            for i in range(len(slices_list)):
                slice_list_all.extend(slices_list[i])
            slice_list_all = [slice_list_all]
            for i in range(len(beats) - 1):
                beat_frame_nums = int(self.default_output_fps * (beats[i+1] - beats[i])) + compensation[i]
                #add face effect on beat less than 2 seconds
                if beat_frame_nums < self.default_output_fps * 2:
                    self.face_effect = "None"#get_random_s(self.face_effect_list)
                    self.convert_effect = get_random_s(self.convert_effect_list)
                    self.screen_effect = "None"
                    slices_list = slice_list_ori
                    slice_frame_nums = beat_frame_nums
                    slice_time = beats[i+1] - beats[i]
                #add screen effect on beat longer than 10 seconds
                elif beat_frame_nums > self.default_output_fps * 10:
                    self.face_effect = "None"
                    self.convert_effect = get_random_s(self.convert_effect_list)
                    self.screen_effect = get_random_s(self.screen_effect_list)
                    slices_list = slice_list_all
                    slice_frame_nums = 0   #pick up any slices, no limit
                    slice_time = 0         #pick up any slices, no limit
                else:
                    self.face_effect = "None"
                    self.screen_effect = "None"
                    self.convert_effect = get_random_s(self.convert_effect_list)
                    slices_list = [slice_list_ori[get_random_i(0,len(slice_list_ori)-1)]]
                    slice_frame_nums = beat_frame_nums
                    slice_time = beats[i+1] - beats[i]
                slice_flow_list, slice_info_list, tmp_file_list = self.prepare_beat_slice_flow(slices_list, slice_frame_nums, slice_time, (base_slice_info["width"],real_height), already_choosen, False)
                combined_slice["%.2f - %.2f: " %(beats[i], beats[i+1])] = already_choosen[-len(slice_flow_list):]
                last_start_width_list = [0] * len(slice_flow_list)
                last_pos_list = [(0,0)] * len(slice_flow_list)
                cur_frame_index = 0
                for j in range(beat_frame_nums):
                    frame, failed_index = self.generate_frame(beat_frame_nums, slice_flow_list, slice_info_list, last_start_width_list, last_pos_list, caption_height, cur_frame_index, (base_slice_info["width"], real_height))
                    while frame == []:
                        if cur_frame_index == 0 or self.screen_effect == "broadcast":
                            #only replace failed part
                            slice_flow_list[failed_index].release()
                            if tmp_file_list[failed_index] != None:
                                os.remove(tmp_file_list[failed_index])
                            slice_flow_failed, slice_info_failed, tmp_file_list_failed = self.prepare_beat_slice_flow(slices_list, slice_frame_nums, slice_time, (base_slice_info["width"],real_height), already_choosen, True)
                            slice_flow_list[failed_index] = slice_flow_failed[0]
                            slice_info_list[failed_index] = slice_info_failed[0]
                            tmp_file_list[failed_index] = tmp_file_list_failed[0]
                        else:
                            self.release_slices(slice_flow_list, tmp_file_list)
                            slice_flow_list, slice_info_list, tmp_file_list = self.prepare_beat_slice_flow(slices_list, slice_frame_nums, slice_time, (base_slice_info["width"],real_height), already_choosen, True)
                        cur_frame_index = 0
                        last_start_width_list = [0] * len(slice_flow_list)
                        last_pos_list = [(0,0)] * len(slice_flow_list)
                        frame, failed_index  = self.generate_frame(beat_frame_nums, slice_flow_list, slice_info_list, last_start_width_list, last_pos_list, caption_height, cur_frame_index, (base_slice_info["width"], real_height))
                    self.write_frame_to_flow(output_flow, frame) 
                    cur_frame_index += 1
                    writed_frames += 1
                    if writed_frames == total_length:
                        self.release_slices(slice_flow_list, tmp_file_list)
                        time_up = True
                        break
                if time_up == True:
                    break
                self.log.log("combine_slices_with_beats", "schedule: %d%%" %((i+1)*100//len(beats)))
            self.log.log("combine_slices_with_beats", "schedule: 100%")
            for i in range(len(tmp_file_list)):
                if tmp_file_list[i] != None:
                    os.remove(tmp_file_list[i])
            for time, slices in combined_slice.items():
                self.log.log("combine_slices_with_beats", time + str(slices))
            output_flow.release()
            return base_slice_info["width"], real_height
        except Exception as e:
            import traceback
            traceback.print_exc()
            output_flow.release()
            exit()
    
    def combine_slices_without_beats(self, slices_list, output_file_name, time, caption_height):
        already_choosen = []
        base_slice_info = self.get_movie_slice_base_info(slices_list)
        real_height = int(base_slice_info["height"] * (1 - caption_height/100))
        writed_frames = 0
        last_start_width_list = [0] * len(slices_list)
        output_flow = cv2.VideoWriter(output_file_name, self.default_output_fourcc, self.default_output_fps, (base_slice_info["width"],real_height))
        total_length = self.default_output_fps * time
        combined_slice = collections.OrderedDict()
        slice_flow_list, slice_info_list = self.prepare_no_beat_slice_flow(slices_list, already_choosen, False)
        cur_frame_index = 0
        schedule = 0
        last_schedule = 0
        i= 0
        last_pos_list = []
        while i < total_length:
            write_frame_nums = 0
            self.convert_effect = get_random_s(self.convert_effect_list)
            need_write_nums = slice_info_list[0]["length"] if (total_length - i > slice_info_list[0]["length"]) else (total_length - i)
            combined_slice["%.2f - %.2f: " %(i / self.default_output_fps, i + slice_info_list[0]["length"] / self.default_output_fps)] = already_choosen[-len(slice_flow_list):]
            for j in range(need_write_nums):
                frame, failed_index = self.generate_frame(need_write_nums, slice_flow_list, slice_info_list, last_start_width_list, last_pos_list, caption_height, cur_frame_index, (base_slice_info["width"], real_height))
                if frame == []:
                    break
                self.write_frame_to_flow(output_flow, frame)
                write_frame_nums += 1
                cur_frame_index += 1
            self.release_slices(slice_flow_list)
            slice_flow_list, slice_info_list = self.prepare_no_beat_slice_flow(slices_list, already_choosen, False)
            cur_frame_index = 0
            i += write_frame_nums
            schedule = i*100//total_length
            if schedule - last_schedule > 1:
                self.log.log("combine_slices_without_beats", "schedule: %d%%" %(schedule))
                last_schedule = schedule
        self.log.log("combine_slices_without_beats", "schedule: 100%")
        for time, slices in combined_slice.items():
            self.log.log("combine_slices_with_beats", time + str(slices))
        output_flow.release()
        return base_slice_info["width"], real_height

    def add_music(self, music_file_list, music_info_list, time, movie_file, final_file):
        music_official_name = music_file_list[0].split('/')[-1]
        music_official_name = '.'.join(music_official_name.split('.')[:-1])
        final_file += '_' + music_official_name + self.default_output_suffix
        music_list = []
        music_time = time
        i = 0
        while music_time > 0:
            if len(music_file_list) == 1 or i == len(music_file_list):
                i = 0
            music = AudioFileClip(music_file_list[i])
            music = audio_fadein.audio_fadein(music, 1)
            if music_info_list[i]["duration"] > music_time:
                music = music.subclip(0, music_time)
                music = audio_fadeout.audio_fadeout(music, 2)
                music_list.append(music)
                break
            else:
                music = audio_fadeout.audio_fadeout(music, 2)
                music_list.append(music)
            music_time -= music_info_list[i]["duration"]
            i += 1
        music = concatenate_audioclips(music_list)
        movie = VideoFileClip(movie_file)
        final = movie.set_audio(music)
        return final, final_file
        
    def add_lrc(self, lrc_json, movie_file, width, height):
        lrc_info = self.painter.get_lrc_json(lrc_json)
        if lrc_info == None:
            self.log.log("add_lrc", "add lrc failed")
            return movie_file
        movie_flow = cv2.VideoCapture(movie_file)
        output_tmp_file = append_file_name(movie_file, "_lrc")
        output_flow = cv2.VideoWriter(output_tmp_file, int(movie_flow.get(cv2.CAP_PROP_FOURCC)), self.default_output_fps, (width,height))
        self.log.log("add_lrc", "adding lrc...")
        lrc_origin = self.painter.get_lrc(lrc_info["id"])
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
        length = int(movie_flow.get(cv2.CAP_PROP_FRAME_COUNT))
        time_list.append(length//self.default_output_fps + 3)
        lrc_list.append("")
        schedule = 0
        last_schedule = -1
        for i in range(length):
            ret, frame = movie_flow.read()
            if ret == False:
                break
            out = self.painter.paint_lrc(time_list, lrc_list, frame, i/self.default_output_fps, (lrc_info["top"], lrc_info["left"]), lrc_info["color"], lrc_info["size"], lrc_info["font"])
            output_flow.write(out)
            schedule = int(i*100/length)
            if schedule - last_schedule > 1:
                self.log.log("add_lrc", "schedule: %d%%" %(schedule))
                last_schedule = schedule
        output_flow.release()
        return output_tmp_file
        
    def make(self, commands, music_file_list, music_info_list, beats, slices_list):
        if os.path.exists(self.output_movie_path) == False:
            os.mkdir(self.output_movie_path)
        movie_file = self.output_movie_path + commands["title"] + self.default_output_suffix
        if commands["beat-mode"] == True:
            width, height = self.combine_slices_with_beats(beats, slices_list, movie_file, commands["time"], float(commands["caption-height"]))
        else:
            width, height = self.combine_slices_without_beats(slices_list, movie_file, commands["time"], float(commands["caption-height"]))
        if commands["lrc"] != None:
            lrc_movie_file = self.add_lrc(commands["lrc"], movie_file, width, height)
            if lrc_movie_file != movie_file:
                os.remove(movie_file)
                movie_file = lrc_movie_file
        if commands["video-only"] == True:
            out_movie_path = append_file_name(movie_file, '_video-only')
            out_movie = VideoFileClip(movie_file)
        else:
            out_movie, out_movie_path = self.add_music(music_file_list, music_info_list, commands["time"], movie_file, self.output_movie_path + commands["title"])
        out_movie = out_movie.fadein(1, (1, 1, 1)).fadeout(2, (1, 1, 1))
        full_movie = []
        make_opening = False
        make_ending = False
        if commands["opconf"] != None:
            opening_movie, opening_file_name = self.painter.add_opening_or_ending("opening", commands["opconf"], out_movie_path, self.default_output_fps, self.default_output_fourcc, width, height)
            if opening_movie == None:
                self.log.log("make", "generate opening failed")
            else:
                full_movie.append(opening_movie)
                make_opening = True
        full_movie.append(out_movie)
        if commands["edconf"] != None:
            ending_movie, ending_file_name = self.painter.add_opening_or_ending("ending", commands["edconf"], out_movie_path, self.default_output_fps, self.default_output_fourcc, width, height)
            if ending_movie == None:
                self.log.log("make", "generate ending failed")
            else:
                full_movie.append(ending_movie)
                make_ending = True
        if len(full_movie) > 1:
            final_movie = concatenate_videoclips(full_movie, method='compose')
        else:
            final_movie = full_movie[0]
        final_path = '.'.join(out_movie_path.split('.')[:-1]) + \
                        ('_op' if make_opening == True else '') + \
                        ('_ed' if make_ending == True else '') + \
                        '.' + out_movie_path.split('.')[-1]
        self.log.log("make", "generating final output file, please wait...")
        final_movie.write_videofile(final_path, codec = self.default_moviepy_codec)
        final_movie.close()
        if make_opening == True:
            os.remove(opening_file_name)
        if make_ending == True:
            os.remove(ending_file_name)
        if os.path.exists(movie_file):
            os.remove(movie_file)
        self.log.log("make", "generating final output file done")
        
    def preprocess_music(self, commands, music_info):
        beats = []
        base_time = 0
        for info in music_info:
            info["beats"].insert(0, 0)
            info["beats"], info["beat_delta"] = self.combine_beats(info["beats"], info["beat_delta"], commands["beat-rate"])
            step = 1
            for i in range(0, len(info["beats"]), step):
                beats.append(info["beats"][i] + base_time)
            base_time += info["duration"]
        while beats[-1] > commands["time"] and beats[-2] > commands["time"]:
            beats.pop(-1)
        while beats[-1] < commands["time"] and beats[-2] < commands["time"]:
            last = beats[-1] + music_info[-1]["beat_delta"]
            beats.append(last)
        return beats
        
    def preprocess_slice(self, commands):
        if self.rec.slice_db == None:
            self.rec.init_slice_database('')
        express_slices = []
        face_size = commands["face-size"] / 100
        for slice, slice_info in self.rec.slice_db[self.rec.slice_path].items():
            if (slice_info["express"] == commands["express"] or commands["express"] == "default") and \
                (commands["feature"] == "" or commands["feature"] in slice) and \
                (slice_info["length"] > commands["slice-size"] * slice_info["fps"]) and \
                (slice_info["length"] <= commands["slice-max-size"] * slice_info["fps"]) and \
                (slice_info["face_percent"] >= face_size):
                    express_slices.append([slice, slice_info])
        if express_slices == []:
            self.log.log("preprocess_slice", "no slices were picked")
        return express_slices
       
    def preprocess_multi_slice(self, commands):
        if self.rec.slice_db == None:
            self.rec.init_slice_database('')
        slices_list = []
        self.combine_mode = commands["multi-mode"]
        for folder in commands["slice-path"]:
            slice_path = self.workarea + folder
            if slice_path[-1] != '/':
                slice_path += '/'
            if slice_path not in self.rec.slice_db.keys():
                self.log.log("preprocess_multi_slice", "folder [%s] not exists in database" %(slice_path))
                return []
            express_slices = []
            face_size = commands["face-size"] / 100
            self.log.log("preprocess_multi_slice", "collecting slices from [%s]" %(slice_path))
            for slice, slice_info in self.rec.slice_db[slice_path].items():
                if (slice_info["express"] == commands["express"] or commands["express"] == "default") and \
                    (commands["feature"] == "" or commands["feature"] in slice) and \
                    (slice_info["length"] > commands["slice-size"] * slice_info["fps"]) and \
                    (slice_info["length"] <= commands["slice-max-size"] * slice_info["fps"]) and \
                    (slice_info["face_percent"] >= face_size):
                        express_slices.append([slice, slice_info])
            if express_slices == []:
                self.log.log("preprocess_multi_slice", "folder [%s] no slices were picked" %(slice_path))
                return []
            slices_list.append(express_slices)
        if self.combine_mode == 'no':
            for i in range(1, len(slices_list)):
                slices_list[0].extend(slices_list[i])
            slices_list = slices_list[:1]
        return slices_list
       
    def make_aragaki_movie(self, commands):
        self.log.log("make_aragaki_movie", "your commands are:\n%s" %(print_dict(commands)))
        if commands["video-only"] == True:
            if commands["time"] == 0:
                total_length = self.rec.get_movie_express_slices_length(commands["express"], rescan = False)
            else:
                total_length = commands["time"]
            music_file, music_info = None, None
            beats = list(range(0, total_length, commands["beat-rate"]))
        else:
            music_file, music_info, total_length = self.get_music(commands["music"])
            if music_info == []:
                return
            else:
                if commands["all-mode"] == True:
                    commands["time"] = self.rec.get_movie_express_slices_length(commands["express"], rescan = False)
                    self.all_mode = True
                if commands["no-repeat"] == True:
                    self.no_repeat = True
                if commands["time"] == 0:
                    self.log.log("make_aragaki_movie", "movie time length using music time length")
                    commands["time"] = int(total_length)
                beats = self.preprocess_music(commands, music_info)
        slices_list = []
        if commands["slice-path"] == []:
            slices = self.preprocess_slice(commands)
            if slices == []:
                return
            slices_list = [slices]
        else:
            slices_list = self.preprocess_multi_slice(commands)
            if slices_list == []:
                return
        output_movie = self.make(commands, music_file, music_info, beats, slices_list)
        
    def cut_scene(self, commands):
        min_size = int(commands["slice-size-range"].split('-')[0])
        max_size = int(commands["slice-size-range"].split('-')[1])
        slices = self.pick_slice(commands, min_size, max_size)
        for slice in slices:
            if os.path.exists(slice[0]) == False:
                continue
            sub_slice_num = 0
            self.log.log("cut_scene", "processing [%s]" %(slice[0]))
            output_tmp_file = append_file_name(slice[0], "_cutscenetmp%d" %(sub_slice_num))
            output_flow = cv2.VideoWriter(output_tmp_file, slice[1]["fourcc"], slice[1]["fps"], (slice[1]["width"],slice[1]["height"]))
            slice_flow = cv2.VideoCapture(slice[0])
            ret, last_frame = slice_flow.read()
            output_flow.write(last_frame)
            write_frame_nums = 1
            while True:
                ret, frame = slice_flow.read()
                if ret == False:
                    break
                if self.rec.compare_scene(frame, last_frame, 20) == True:
                    write_frame_nums += 1
                elif write_frame_nums != 0:
                    new_slice_info = copy.deepcopy(slice[1])
                    new_slice_info["length"] = write_frame_nums
                    self.rec.update_slice_db(output_tmp_file, new_slice_info, commands['slice-path'], predict = True)
                    output_flow.release()
                    sub_slice_num += 1
                    write_frame_nums = 0
                    output_tmp_file = append_file_name(slice[0], "_cutscenetmp%d" %(sub_slice_num))
                    self.log.log("cut_scene", "openging new output file [%s]" %(output_tmp_file))
                    output_flow = cv2.VideoWriter(output_tmp_file, slice[1]["fourcc"], slice[1]["fps"], (slice[1]["width"],slice[1]["height"]))
                output_flow.write(frame)
                last_frame = frame
            self.log.log("cut_scene", "[%s] cut successful" %(slice[0]))
            #self.rec.update_slice_db(slice[0], None, commands['path'], operation = "del", predict = True)
            slice_flow.release()
            output_flow.release()
        
    def cut_slices(self, commands):
        min_size = int(commands["slice-size-range"].split('-')[0])
        max_size = int(commands["slice-size-range"].split('-')[1])
        slices = self.pick_slice(commands, min_size, max_size)
        for slice in slices:
            if os.path.exists(slice[0]) == False:
                continue
            sub_frame_nums = commands["slice-size"] * slice[1]["fps"]
            origin_length = slice[1]["length"]
            slice_flow = cv2.VideoCapture(slice[0])
            sub_slice_nums = 0
            while origin_length > sub_frame_nums:
                new_slice_info = copy.deepcopy(slice[1])
                output_tmp_file = append_file_name(slice[0], "_cut%d" %(sub_slice_nums))
                self.log.log("cut_slices", "openging new output file [%s]" %(output_tmp_file))
                output_flow = cv2.VideoWriter(output_tmp_file, slice[1]["fourcc"], slice[1]["fps"], (slice[1]["width"],slice[1]["height"]))
                for i in range(sub_frame_nums):
                    ret, frame = slice_flow.read()
                    output_flow.write(frame)
                sub_slice_nums += 1
                origin_length -= sub_frame_nums
                new_slice_info["length"] = sub_frame_nums
                output_flow.release()
                self.rec.update_slice_db(output_tmp_file, new_slice_info, commands['path'], predict = True)
            #if remain less than 1 second, drop it
            if origin_length >= slice[1]["fps"]:
                new_slice_info = copy.deepcopy(slice[1])
                output_tmp_file = append_file_name(slice[0], "_cut%d" %(sub_slice_nums))
                output_flow = cv2.VideoWriter(output_tmp_file, slice[1]["fourcc"], slice[1]["fps"], (slice[1]["width"],slice[1]["height"]))
                for i in range(origin_length):
                    ret, frame = slice_flow.read()
                    output_flow.write(frame)
                sub_slice_nums += 1
                new_slice_info["length"] = origin_length
                self.rec.update_slice_db(output_tmp_file, new_slice_info, commands['path'], operation = "add", predict = True)
            output_flow.release()
            slice_flow.release()
            #self.rec.update_slice_db(slice[0], None, commands['path'], operation = "del", predict = False)
            self.log.log("cut_slices", "[%s] cut to %s sub slices successful" %(slice[0], sub_slice_nums))
        
    def cut_size(self, commands):
        min_size = int(commands["slice-size-range"].split('-')[0])
        max_size = int(commands["slice-size-range"].split('-')[1])
        slices = self.pick_slice(commands, min_size, max_size)
        for slice in slices:
            if os.path.exists(slice[0]) == False:
                continue
            if commands["top-cut"] + commands["bottom-cut"] > slice[1]["height"] or \
                commands["left-cut"] + commands["right-cut"] > slice[1]["width"]:
                continue
            self.log.log("cut_slices","processing [%s]" %(slice[0]))
            slice_flow = cv2.VideoCapture(slice[0])
            output_tmp_file = append_file_name(slice[0], "_cutsizetmp")
            output_height = slice[1]["height"] - commands["top-cut"] - commands["bottom-cut"]
            output_width = slice[1]["width"] - commands["left-cut"] - commands["right-cut"]
            output_flow = cv2.VideoWriter(output_tmp_file, slice[1]["fourcc"], slice[1]["fps"], (output_width,output_height))
            while True:
                ret, frame = slice_flow.read()
                if ret == False:
                    break
                final = frame[commands["top-cut"]:frame.shape[0] - commands["bottom-cut"],commands["left-cut"]:frame.shape[1] - commands["right-cut"]]
                output_flow.write(final)
            slice_flow.release()
            output_flow.release()
            slice[1]["height"] = slice[1]["height"] - commands["top-cut"] - commands["bottom-cut"]
            slice[1]["width"] = slice[1]["width"] - commands["left-cut"] - commands["right-cut"]
            self.log.log("cut_slices", "[%s] cut successfully" %(slice[0]))
            self.log.log("cut_slices", "output file is [%s]" %(output_tmp_file))
            
    def slomo_slice(self, commands):
        min_size = int(commands["slice-size-range"].split('-')[0])
        max_size = int(commands["slice-size-range"].split('-')[1])
        slice_list = self.pick_slice(commands, min_size, max_size)
        times = float(commands["slow-times"])
        for slice in slice_list:
            if os.path.exists(slice[0]) == False:
                continue
            self.log.log("slomo_slice", "processing file [%s]" %(slice[0]))
            slice_flow = cv2.VideoCapture(slice[0])
            output_file = append_file_name(slice[0], "_slomo")
            output_flow = cv2.VideoWriter(output_file, slice[1]["fourcc"], slice[1]["fps"], (slice[1]["width"],slice[1]["height"]))
            frames = []
            for i in range(slice[1]["length"]):
                ret, frame = slice_flow.read()
                if ret == False:
                    break
                frames.append(copy.deepcopy(frame))
            for i in range(int(slice[1]["length"]*times)):
                index = int(1/times*i)
                if index > len(frames) - 1:
                    index = len(frames) - 1
                output_flow.write(frames[index])
            slice_flow.release()
            output_flow.release()
            self.log.log("slomo_slice", "[%s] slomo successfully" %(slice[0]))
            
    def cut_face(self, commands):
        import face_recognition as fr
        min_size = int(commands["slice-size-range"].split('-')[0])
        max_size = int(commands["slice-size-range"].split('-')[1])
        self.rec.init_picture_database()
        slice_list = self.pick_slice(commands, min_size, max_size)
        for slice in slice_list:
            if os.path.exists(slice[0]) == False:
                continue
            self.log.log("cut_face", "processing file [%s]" %(slice[0]))
            slice_flow = cv2.VideoCapture(slice[0])
            output_file = append_file_name(slice[0], "_cutface")
            face_hit_num = [0] * len(self.rec.pic_db)
            match_face = 0
            for i in range(slice[1]["length"]//slice[1]["fps"]):
                frames = self.rec.load_frame(slice_flow, slice[1]["fps"])
                if frames == []:
                    break
                face_locations = fr.face_locations(frames[0])
                if self.rec.compare_face(frames[0], face_locations, slice[1]["width"], slice[1]["height"], face_hit_num) == True:
                    if i == 0 or i == 1:
                        match_face = 2
                        break
                    slice_flow.set(cv2.CAP_PROP_POS_FRAMES, (i-1)*slice[1]["fps"])
                    frames = self.rec.load_frame(slice_flow, slice[1]["fps"])
                    for j in range(len(frames) - 1, 0, -1):
                        face_locations = fr.face_locations(frames[j])
                        if self.rec.compare_face(frames[j], face_locations, slice[1]["width"], slice[1]["height"], face_hit_num) != True:
                            break
                    slice_flow.set(cv2.CAP_PROP_POS_FRAMES, (i-1)*slice[1]["fps"]+j+2)
                    match_face = 1
                    break
            if match_face == 1:
                output_flow = cv2.VideoWriter(output_file, slice[1]["fourcc"], slice[1]["fps"], (slice[1]["width"],slice[1]["height"]))
                output_flow.write(frames[0])
                while True:
                    ret, frame = slice_flow.read()
                    if ret == False:
                        break
                    output_flow.write(frame)
                output_flow.release()
                self.log.log("cut_face", "[%s] cut successfully" %(slice[0]))
            elif match_face == 2:
                self.log.log("cut_face", "[%s] do not need to cut" %(slice[0]))
            else:
                self.log.log("cut_face", "[%s] detect face failed" %(slice[0]))
            slice_flow.release()
    