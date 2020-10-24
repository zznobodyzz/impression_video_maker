from any2mp3 import any2mp3
import librosa
import numpy as np
import os
import copy
from utils import *
import pygame
import time


class Mus():
    def __init__(self, log, cfg):
        self.log = log
        self.workarea = cfg.get_cfg("main", "workarea")
        self.music_path = self.workarea + cfg.get_cfg("listen", "music_path")
        self.music_beat_path = self.workarea + cfg.get_cfg("listen", "music_beat_path")
        self.music_database = self.workarea + cfg.get_cfg("listen", "music_database")
        #{music_name : {beats, beat_delta, duration}}
        self.mus_db = None
    
    def counter_delta_times(self, delta, limit):
        counter = dict()
        deltad = copy.deepcopy(delta)
        i = 0
        length = len(deltad)
        while i < length:
            d = deltad[i]
            delta_tmp = copy.deepcopy(deltad)
            delta_tmp.pop(delta_tmp.index(d))
            for dt in delta_tmp:
                if dt < d:
                    if d - dt < d * limit:
                        if d in counter.keys():
                            counter[d].append(dt)
                        else:
                            counter[d] = [d, dt]
                        deltad.pop(deltad.index(dt))
                elif d < dt:
                    if dt - d < d * limit:
                        if d in counter.keys():
                            counter[d].append(dt)
                        else:
                            counter[d] = [d, dt]
                        deltad.pop(deltad.index(dt))
                else:
                    if d in counter.keys():
                        counter[d].append(dt)
                    else:
                        counter[d] = [d, dt]
                    deltad.pop(deltad.index(dt))
            i += 1
            length = len(deltad)
        return counter
    
    def format_beats(self, beats, counter):
        beat_nums = dict()
        for c in counter.keys():
            beat_nums[c] = len(counter[c])
        max = 0
        for b in beat_nums.keys():
            if beat_nums[b] > max:
                selete_beat = b
                max = beat_nums[b]
        selete_beat_avg = sum(counter[selete_beat])/len(counter[selete_beat])
        i = 0
        length = len(beats) - 1
        while i < length:
            if beats[i + 1] - beats[i] < selete_beat_avg * 0.9:
                beats.pop(i)
                length = len(beats) - 1
            else:
                i += 1
        if beats[-1] - beats[-2] < selete_beat_avg * 0.9:
            beats.pop(-1)
        i = 0
        length = len(beats) - 1
        while i < length:
            if (beats[i + 1] - beats[i] > selete_beat_avg * 2 * 0.8):
                beats.insert(i + 1, beats[i] + selete_beat_avg)
                length = len(beats) - 1
            i += 1
        return beats, selete_beat_avg
        
    def check_data_diff(self, data_list):
        avg = sum(data_list)/len(data_list)
        for data in data_list:
            if data > avg:
                if data - avg > avg * 0.1:
                    return True
            elif data < avg:
                if avg - data > avg * 0.1:
                    return True
        return False
        
    def predict_delta_law(self, delta):
        max_try = 5
        i = 0
        while i < 20:
            for m in range(1, max_try):
                sum1 = []
                sum2 = []
                sum3 = []
                not_match = False
                for n in range(m):
                    sum1.append(delta[i+n])
                for n in range(m):
                    sum2.append(delta[i+m+n])
                for n in range(m):
                    sum3.append(delta[i+m+m+n])
                for s1, s2, s3 in zip(sum1, sum2, sum3):
                    if self.check_data_diff([s1, s2, s3]) == True:
                        not_match = True
                        break
                if not_match == False:
                    return i, m
            i += 1
        return None, None
           
    def combine_delta(self, beats, delta, tempo, index):
        i = index
        delta_result = copy.deepcopy(delta)
        suma = sum(tempo)
        length = len(delta_result)
        while i < length - len(tempo):
            not_match = False
            for j in range(len(tempo)):
                if self.check_data_diff([delta_result[i+j], tempo[j]]) == True:
                    not_match = True
                    break
            if not_match == False and len(tempo) != 1:
                for k in range(len(tempo)):
                    delta_result.pop(i)
                    beats.pop(i + 1)
                delta_result.insert(i, suma)
                beats.insert(i + 1, beats[i] + suma)
            i += 1
            length = len(delta_result)
        return beats, delta_result
        
    def get_music_beats(self, y, sr):
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512, aggregate=np.median)
        peaks = librosa.util.peak_pick(onset_env, 1, 1, 1, 1, 0.8, 5)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        M = beats * [[1 / 4], [2 / 4], [3 / 4]]
        M = M.flatten()
        M = np.sort(M)
        L = []
        for i in M:
            for j in peaks:
                if i * 0.9 < j < i * 1.1:
                    L.append(j)
        L = list(set(L))
        L.sort()
        beats = (librosa.frames_to_time(L, sr=sr)).tolist()
        delta = []
        delta_int = []
        for i in range(len(beats)-1):
            delta.append(beats[i + 1] - beats[i])
            delta_int.append(round(beats[i + 1] - beats[i], 2))
        index, nums = self.predict_delta_law(delta_int)
        if index == None:   
            self.log.log("predict_delta_law", "predict_delta_law failed")
            index = 0 
            nums = 1
        beats, delta = self.combine_delta(beats, delta, delta[index:index+nums], index)
        counter = self.counter_delta_times(delta, 0.1)
        beats, base_delta = self.format_beats(beats, counter)
        delta = []
        for i in range(len(beats)-1):
            delta.append(beats[i + 1] - beats[i])
        return beats, base_delta
        
    def get_music_duration(self, y, sr):
        return librosa.get_duration(y, sr)
        
    def init_music_database(self):
        if self.mus_db != None:
            return
        if os.path.exists(self.music_database) == False:
            self.log.log("init_music_database", "no mus_db found, use new db")
            self.mus_db = dict()
        else:
            self.mus_db = load_pkl(self.music_database)
            if self.mus_db == None:
                self.log.log("init_music_database", "mus_db is empty, use new db")
                self.mus_db = dict()
            else:
                self.log.log("init_music_database", "found mus_db, going to use it")
        
    def save_music_database(self):
        save_pkl(self.music_database, self.mus_db)
        
    def convert_mus_type(self, file_path):
        if file_path.split(".")[-1] != "mp3":
            new_file_path = ".".join(file_path.split(".")[:-1]) + ".mp3"
            any2mp3(file_path, new_file_path)
            os.remove(file_path)
            self.log.log("convert_mus_type", "converted [%s] to [%s], [%s] has been deleted automatically" %(file_path, new_file_path, file_path))
            return new_file_path.split('/')[-1]
        else:
            return file_path.split('/')[-1]
        
    def generate_music_beats(self, file):
        pygame.mixer.init()
        print(file)
        pygame.mixer.music.load(file)
        pygame.mixer.music.set_volume(0.7)
        print("press enter to record beats while playing music")
        print("press r and enter to restart playing music")
        print("warning: need to set focus to python command window after starting playing music")
        time.sleep(2)
        print("3")
        time.sleep(1)
        print("2")
        time.sleep(1)
        print("1")
        time.sleep(1)
        #must set mode, otherwise music will not start
        pygame.display.set_mode([100,100])
        pygame.mixer.music.play()
        oldtime = time.time()
        beats = []
        while pygame.mixer.music.get_busy():
            a = input()
            nowtime = time.time()
            print(nowtime - oldtime)
            beats.append(nowtime - oldtime)
            if a == 'r':
                pygame.mixer.music.rewind()
                beats = []
                oldtime = time.time()
        return beats, sum(beats)/len(beats)
        
    def check_new_mus(self, rescan, beat_detect_mode):
        if os.path.exists(self.music_path) == False:
            os.mkdir(self.music_path)
            self.log.log("check_new_mus", "folder %s not exists, created automatically, this may be your first time running this program, please try to find some music and put them into folder %s" %(self.music_path,self.music_path))
            return
        new_file = []
        current_mus = [mus for mus in os.listdir(self.music_path)]
        for mus in list(self.mus_db):
            if mus not in current_mus:
                self.log.log("check_new_mus", "origin file [%s] not found, delete it from database" %(mus))
                self.mus_db.pop(mus)
        for file in os.listdir(self.music_path):
            if file not in self.mus_db.keys() or rescan == True:
                self.log.log("check_new_mus", "processing music file [%s]" %(file))
                file = self.convert_mus_type(self.music_path+file)
                self.mus_db[file] = dict()
                if beat_detect_mode == "auto":
                    if file in os.listdir(self.music_beat_path):
                        self.log.log("check_new_mus", "found beat file, using it for beat tracking")
                        beat_file = self.music_beat_path+file
                        self.convert_mus_type(beat_file)
                    else:
                        beat_file = self.music_path+file
                    y, sr = librosa.load(self.music_path+file)
                    self.mus_db[file]["duration"] = self.get_music_duration(y, sr)
                    self.mus_db[file]["beats"] = [3.904,7.527,11.154,14.744,18.393,21.927,25.561,29.238,30.964,32.807,34.581,36.398,38.197,40.008,41.795,43.584,45.357,47.253,49.021,50.846,52.636,54.46,56.241,58.3,59.763,61.66,63.431,65.244,67.07,68.892,70.685,72.486,76.116,79.799,83.353,86.899,90.537,94.116,97.732,101.34,104.957,108.579,112.182,115.81,117.616,119.419,121.23,123.013,124.817,126.65,128.37,130.194,132.047,133.836,135.669,137.46,139.258,141.03,142.84,144.716,148.336,151.914,155.526,159.13,162.7,166.293,169.941,173.554,177.188,180.794,184.418,188.036,191.63,195.21,198.811,202.484,208.309,212.753]
                    self.mus_db[file]["beat_delta"] = 7.527 - 3.904
                    #self.mus_db[file]["beats"], self.mus_db[file]["beat_delta"] = self.get_music_beats(y, sr)
                else:
                    y, sr = librosa.load(self.music_path+file)
                    self.mus_db[file]["duration"] = self.get_music_duration(y, sr)
                    self.mus_db[file]["beats"], self.mus_db[file]["beat_delta"] = self.generate_music_beats(self.music_path + file)
                while self.mus_db[file]["beats"][-1] < self.mus_db[file]["duration"]:
                    self.mus_db[file]["beats"].append(self.mus_db[file]["beats"][-1] + self.mus_db[file]["beat_delta"])
                if self.mus_db[file]["beat_delta"] < 1:
                    self.mus_db[file]["style"] = "fast"
                else:
                    self.mus_db[file]["style"] = "slow"
                new_file.append(file)
        if new_file != []:
            self.log.log("check_new_mus", "successfully loaded %d songs" %(len(new_file)))
            self.log.log("check_new_mus", "they are [" + " ".join(new_file) + "]")
        
    def find_music(self, rescan, beat_detect_mode):
        self.init_music_database()
        self.check_new_mus(rescan, beat_detect_mode)
        self.save_music_database()
        
    def get_random_music(self):
        self.init_music_database()
        if len(self.mus_db.keys()) != 0:
            return get_random_s(self.mus_db.keys())
        else:
            return None
    