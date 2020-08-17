import os
from utils import *
import face_recognition as fr
import cv2
import copy
import traceback
from any2jpg import any2jpg
    
class Rec():
    def __init__(self, log, recexp):
        self.recexp = recexp
        self.workarea = "./wa/"
        self.log = log
        self.picture_path = self.workarea + "pic_of_gaki/"
        self.picture_database = self.workarea + "pic_db.pkl"
        self.video_path = self.workarea + "video_of_gaki/"
        self.video_database = self.workarea + "video_db.pkl"
        self.slice_path = self.workarea + "slice_video/"
        self.slice_database = self.workarea + "slice_db.pkl"
        #pic_db [[image name,image face encodings]]
        self.pic_db = None
        #video_db {video name : {total_length, height, width, fps, fourcc, schedule}}
        self.video_db = None
        self.old_video_db = None
        #slice_db {slice_name : {express, length, height, width, fps, fourcc}}
        self.slice_db = None
        self.default_scene_confidence = 15
        self.default_face_confidence = 0.45
        if os.path.exists(self.workarea) == False:
            os.mkdir(self.workarea)
        
    def init_picture_database(self):
        if self.pic_db != None:
            return
        if os.path.exists(self.picture_database) == False:
            self.log.log("init_picture_database", "no pic_db found, use new db")
            self.pic_db = list()
        else:
            self.pic_db = load_pkl(self.picture_database)
            if self.pic_db == None:
                self.log.log("init_picture_database", "pic_db is empty, use new db")
                self.pic_db = list()
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
        
    def check_new_pic(self, rescan):
        if os.path.exists(self.picture_path) == False:
            os.mkdir(self.picture_path)
            self.log.log("check_new_pic", "folder %s not exists, created automatically, this may be your first time running this program, please try to find some pictures and put them into folder %s" %(self.picture_path,self.picture_path))
            return
        current_pics = [(self.video_path + current_pic) for current_pic in os.listdir(self.picture_path)]
        for pic in self.pic_db:
            if pic[0] not in current_pics:
                self.log.log("check_new_pic", "origin file [%s] not found, delete it from database" %(pic[0]))
                self.pic_db.pop(pic)
        new_file = []
        for file in os.listdir(self.picture_path):
            if rescan == False:
                already_loaded = False
                for pics in self.pic_db:
                    if file == pics[0]:
                        already_loaded = True
                        break
                if already_loaded == True:
                    continue
            file = self.convert_pic_type(self.picture_path+file)
            image = fr.load_image_file(self.picture_path+file)
            face_locations = fr.face_locations(image)
            #only handle one person frame
            if face_locations == []:
                self.log.log("check_new_pic", "[%s] no face detected, not our goals" %(file))
                continue
            if len(face_locations) != 1:
                self.log.log("check_new_pic", "[%s] detected several faces, not our goals" %(file))
                continue
            face_encodings = fr.face_encodings(image, face_locations)
            pic_dict = [file, face_encodings]
            self.pic_db.append(copy.deepcopy(pic_dict))
            new_file.append(file)
        if new_file != []:
            self.log.log("check_new_pic", "successfully loaded %d images" %(len(new_file)))
            self.log.log("check_new_pic", "they are [" + " ".join(new_file) + "]")
        
    def learn_aragaki(self, rescan):
        self.init_picture_database()
        self.check_new_pic(rescan)
        self.save_picture_database()
        
    def init_video_database(self):
        if self.video_db != None:
            return
        if os.path.exists(self.video_database) == False:
            self.log.log("init_video_database", "no video_db found, use new db")
            self.video_db = dict()
        else:
            self.video_db = load_pkl(self.video_database)
            if self.video_db == None:
                self.log.log("init_video_database", "video_db is empty, use new db")
                self.video_db = dict()
            else:
                self.log.log("init_video_database", "found video_db, going to use it")
        self.old_video_db = copy.deepcopy(self.video_db)
            
    def init_slice_database(self):
        if self.slice_db != None:
            return
        if os.path.exists(self.slice_database) == False:
            self.log.log("init_slice_database", "no slice_db found, use new db")
            self.slice_db = dict()
        else:
            self.slice_db = load_pkl(self.slice_database)
            if self.slice_db == None:
                self.log.log("init_slice_database", "slice_db is empty, use new db")
                self.slice_db = dict()
            else:
                self.log.log("init_slice_database", "found slice_db, going to use it")
        if os.path.exists(self.slice_path) == False:
            os.mkdir(self.slice_path)
        
    def save_video_database(self):
        save_pkl(self.video_database, self.video_db)
        
    def save_slice_database(self):
        save_pkl(self.slice_database, self.slice_db)
        
    def check_new_video(self):
        if os.path.exists(self.video_path) == False:
            os.mkdir(self.video_path)
            self.log.log("check_new_video", "folder %s not exists, created automatically, this may be your first time running this program, please try to find some video and put them into folder %s" %(self.video_path,self.video_path))
            return
        current_videos = [(self.video_path + current_video) for current_video in os.listdir(self.video_path)]
        for video in list(self.video_db):
            if video not in current_videos:
                self.log.log("check_new_video", "origin file [%s] not found, delete it from database" %(video))
                self.video_db.pop(video)
        new_file = []
        for file in os.listdir(self.video_path):
            file_path = self.video_path+file
            if file_path not in self.video_db.keys():
                self.video_db[file_path] = dict()
                flow = cv2.VideoCapture(file_path)
                self.video_db[file_path]["length"] = int(flow.get(cv2.CAP_PROP_FRAME_COUNT))
                self.video_db[file_path]["width"] = int(flow.get(cv2.CAP_PROP_FRAME_WIDTH))
                self.video_db[file_path]["height"] = int(flow.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.video_db[file_path]["fps"] = int(flow.get(cv2.CAP_PROP_FPS))
                self.video_db[file_path]["fourcc"] = int(flow.get(cv2.CAP_PROP_FOURCC))
                self.video_db[file_path]["schedule"] = 0
                self.video_db[file_path]["match_num"] = 0
                new_file.append(file)
                flow.release()
        if new_file != []:
            self.log.log("check_new_video", "successfully loaded %d videos" %(len(new_file)))
            self.log.log("check_new_video", "they are [" + " ".join(new_file) + "]")
    
    def update_slice_db(self, slice_name, slice_info, operation = "add", predict = False):
        self.init_slice_database()
        if operation == "del":
            del self.slice_db[slice_name]
            self.save_slice_database()
        if predict == True:
            flow = cv2.VideoCapture(slice_name)
            slice_info["express"] = self.recexp.predict_flow(flow, slice_info["length"])
        self.slice_db[slice_name] = slice_info
        self.save_slice_database()
        
    def sync_slice_info(self):
        self.init_slice_database()
        if os.path.exists(self.slice_path) == False:
            os.mkdir(self.slice_path)
            return
        self.recexp.load_recognizer()
        current_slices = [(self.slice_path + current_slice) for current_slice in os.listdir(self.slice_path)]
        for slice in list(self.slice_db):
            if slice not in current_slices:
                self.log.log("sync_slice_info", "origin file [%s] not found, delete it from database" %(slice))
                self.slice_db.pop(slice)
        for file_path in current_slices:
            if file_path not in self.slice_db.keys():
                self.log.log("sync_slice_info", "new file found [%s]" %(file_path))
                flow = cv2.VideoCapture(file_path)
                '''
                express_result = [file_path.find(i) for i in self.recexp.label_define]
                if max(express_result) != -1:
                    express = self.recexp.label_define[express_result.index(max(express_result))]
                    new_file_path = file_path
                else:
                    ret, frame = flow.read()
                    express = self.recexp.predict_image(frame)
                    new_file_path = append_file_name(file_path, express)
                '''
                new_file_path = file_path
                express = "default"
                self.slice_db[new_file_path] = dict()
                self.slice_db[new_file_path]["length"] = int(flow.get(cv2.CAP_PROP_FRAME_COUNT))
                self.slice_db[new_file_path]["width"] = int(flow.get(cv2.CAP_PROP_FRAME_WIDTH))
                self.slice_db[new_file_path]["height"] = int(flow.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.slice_db[new_file_path]["fps"] = int(flow.get(cv2.CAP_PROP_FPS))
                self.slice_db[new_file_path]["fourcc"] = int(flow.get(cv2.CAP_PROP_FOURCC))
                self.slice_db[new_file_path]["express"] = express
                self.slice_db[new_file_path]["face_percent"] = 100
                flow.release()
                if new_file_path != file_path:
                    os.rename(file_path, new_file_path)
                    self.log.log("sync_slice_info", "renamed the file automatically")
        self.save_slice_database()
        self.log.log("sync_slice_info", "sync_slice_info done")
        
    def open_slice_video(self, flow_file, origin_video_info, start_second, face_location):
        codec = origin_video_info["fourcc"]
        fourcc = cv2.VideoWriter_fourcc(chr(codec&0xFF), chr((codec>>8)&0xFF), chr((codec>>16)&0xFF), chr((codec>>24)&0xFF))
        file_name = flow_file.split('/')[-1]
        file_name = '.'.join(file_name.split('.')[:-1])
        slice_file_name = self.slice_path+file_name+'_'+str(start_second)+"s"
        if os.path.exists(slice_file_name + '.avi') == True:
            i = 1
            while True:
                slice_file_name += '_' + str(i)
                if os.path.exists(slice_file_name + '.avi') == False:
                    break
                slice_file_name = slice_file_name[:len(slice_file_name) - len(str(i)) - 1]
                i += 1
        slice_file_name += '.avi'
        self.log.log("open_slice_video", "the current slice video is [%s]" %(slice_file_name))
        slice_flow = cv2.VideoWriter(slice_file_name, fourcc, origin_video_info["fps"], (origin_video_info["width"],origin_video_info["height"]))
        self.slice_db[slice_file_name] = dict()
        self.slice_db[slice_file_name]["length"] = 0
        self.slice_db[slice_file_name]["width"] = origin_video_info["width"]
        self.slice_db[slice_file_name]["height"] = origin_video_info["height"]
        self.slice_db[slice_file_name]["fps"] = origin_video_info["fps"]
        self.slice_db[slice_file_name]["fourcc"] = origin_video_info["fourcc"]
        self.slice_db[slice_file_name]["face_percent"] = (face_location[3] - face_location[1])/origin_video_info["width"]
        return slice_flow, slice_file_name
        
    def close_slice_video(self, slice_flow, file_path):
        if slice_flow == None:
            return
        slice_flow.release()
        slice_flow = cv2.VideoCapture(file_path)
        self.slice_db[file_path]["length"] = int(slice_flow.get(cv2.CAP_PROP_FRAME_COUNT))
        #self.slice_db[file_path]["express"] = self.recexp.predict_flow(slice_flow, self.slice_db[file_path]["length"])
        self.slice_db[file_path]["express"] = "default"
        slice_flow.release()
        self.save_slice_database()
        
    def ahash(self, frame):
        frame=cv2.resize(frame, (8,8), interpolation=cv2.INTER_CUBIC)
        gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        s = 0
        hash_str = ''
        for i in range(8):
            for j in range(8):
                s = s + gray[i,j]
        avg = s/64
        for i in range(8):
            for j in range(8):
                if gray[i,j] > avg:
                    hash_str = hash_str+'1'
                else:
                    hash_str = hash_str + '0'
        return hash_str
        
    def face_location_check(self, face_locations, width, height):
        #not in the center of the picture
        if (face_locations[1] < width//5 and face_locations[3] > width//5*4) or \
            (face_locations[1] > width//5*4 and face_locations[3] < width//5):
            return False
        
    def compare_face(self, frame, face_locations, width, height, face_hit_num):
        #only handle one person frame
        if len(face_locations) != 1:
            return False
        face_encodings = fr.face_encodings(frame, face_locations)
        for pic in self.pic_db:
            match = fr.compare_faces(pic[1], face_encodings[0], tolerance=self.default_face_confidence)
            if match[0] == True:
                #if self.face_location_check(face_locations[0], width, height) == False:
                    #return False
                face_hit_num[self.pic_db.index(pic)] += 1
                #frame = cv2.UMat().get()
                #cv2.rectangle(frame, (face_locations[0][3], face_locations[0][0]), (face_locations[0][1], face_locations[0][2]), (0, 0, 255), 2)
                return True
        return False
        
    def compare_scene(self, frame1, frame2, confidence):
        if len(frame1) == 0:
            return True
        hash1 = self.ahash(frame1)
        hash2 = self.ahash(frame2)
        n=0
        for i in range(len(hash1)):
            if hash1[i] != hash2[i]:
                n += 1
        #half different
        if n > confidence:
            return False
        return True
        
    def load_frame(self, flow, nums):
        rgb_frame = []
        for i in range(nums):
            ret, frame = flow.read()
            if ret == False:
                break
            rgb_frame.append(frame[:, :, ::-1])
        return rgb_frame
        
    def write_slice_video(self, frames, slice_flow):
        if slice_flow == None:
            return
        for frame in frames:
            slice_flow.write(frame)
        
    def process_frame(self, frames):
        #rgb <-> bgr
        for i in range(len(frames)):
            frames[i] = frames[i][:, :, ::-1]
        return frames
        
    def update_schedule(self, flow_file, schedule, match_num):
        self.video_db[flow_file]["schedule"] = schedule
        self.video_db[flow_file]["match_num"] = match_num
        self.save_video_database()
        
    def get_job_result(self):
        worked_job = []
        if self.video_db == {}:
            return
        if self.old_video_db == {}:
            for flow_name, sc in self.video_db.items():
                worked_job.append("new job:[%s] pushed to %s, match percent: %.2f%%" %(flow_name, sc["schedule"], sc["match_num"]*100//sc["length"]))
            return
        for flow_name, old_sc in self.old_video_db.items():
            if old_sc["schedule"] == "100%":
                continue
            if self.video_db[flow_name]["schedule"] > old_sc["schedule"]:
                worked_job.append("old job:[%s] pushed from %d%% to %d%%, match percent: %.2f%%" %(flow_name, old_sc["schedule"], self.video_db[flow_name]["schedule"], self.video_db[flow_name]["match_num"]*100//self.video_db[flow_name]["length"]))
        for flow_name, sc in self.video_db.items():
            if flow_name not in self.old_video_db.keys():
                worked_job.append("new job:[%s] pushed to %s, match percent: %.2f%%" %(flow_name, sc["schedule"], sc["match_num"]*100//sc["length"]))
        for job in worked_job:
            self.log.log("get_job_result", job)
    
    def reorder_faces(self, face_hit_num):
        face_hit_num_tmp = copy.deepcopy(face_hit_num)
        pic_db_tmp = []
        for i in range(len(face_hit_num)):
            index = face_hit_num_tmp.index(max(face_hit_num_tmp))
            pic_db_tmp.append(self.pic_db[index])
            face_hit_num_tmp[index] = -1
        self.pic_db = copy.deepcopy(pic_db_tmp)
    
    def trans_seconds_to_time(self, seconds):
        return "min".join([str(seconds//60),str(seconds%60)]) + 'sec'
    
    def start_fuzzy_job(self, mode, min_second):
        now_schedule = 0
        current_slice_flow = None
        flow_path = ""
        flow = None
        index = 0
        batch_size = 0
        face_hit_num = [0] * len(self.pic_db)
        for flow_file, info in self.video_db.items():
            try:
                if info["schedule"] == 100:
                    continue
                last_schedule = 0
                total_time = self.trans_seconds_to_time(info["length"]//info["fps"])
                self.log.log("start_fuzzy_job", "start processing video [%s]" %(flow_file))
                write_frame_nums = 0
                batch_size = min_second * info["fps"]
                match_num = 0
                flow = cv2.VideoCapture(flow_file)
                is_done = False
                if info["schedule"] != 0:
                    start_index = int(info["schedule"]/100 * info["length"])
                    flow.set(cv2.CAP_PROP_POS_FRAMES, int(info["schedule"]/100 * info["length"]))
                    self.log.log("start_fuzzy_job", "continue with schedule %d\n" %(info["schedule"]))
                else:
                    start_index = 0
                last_success_frame = []
                last_success_frame_index = -2
                #batch
                for index in range(start_index//batch_size, info["length"]//batch_size):
                    success = False
                    frames = self.load_frame(flow, batch_size)
                    if frames == []:
                        is_done = True
                        break
                    #if the first frame matched, check the last frame
                    #(top, right, bottom, left)
                    face_locations = fr.face_locations(frames[0])
                    face_match = self.compare_face(frames[0], face_locations, info["width"], info["height"], face_hit_num)
                    if face_match == True:
                        if mode == "fuzzy":
                            #check 1/2 of the batch until match
                            for i in range(len(frames) - 1, len(frames)//2 - 1, -1):
                                face_locations = fr.face_locations(frames[i])
                                if self.compare_face(frames[i], face_locations, info["width"], info["height"], face_hit_num) == True:
                                    success = True
                                    #if in different scene, drop the tail
                                    if ((i != len(frames) - 1) and (self.compare_scene(frames[i], frames[i+1], self.default_scene_confidence) == False)):
                                        frames = frames[:i+1]
                                    break
                        elif mode == "fastest":
                            face_locations = fr.face_locations(frames[-1])
                            if self.compare_face(frames[-1], face_locations, info["width"], info["height"], face_hit_num) == True:
                                face_locations = fr.face_locations(frames[len(frames)//2])
                                if self.compare_face(frames[-1], face_locations, info["width"], info["height"], face_hit_num) == True:
                                    success = True
                    #this batch is matched
                    if success == True:
                        final_frames = self.process_frame(frames)
                        #if the same scene
                        if (index * batch_size - last_success_frame_index == 1) and \
                            (self.compare_scene(last_success_frame, frames[0], self.default_scene_confidence) == True):
                            #write it right behind the last video
                            write_frame_nums += len(final_frames)
                        #else if different scene
                        else:
                            self.close_slice_video(current_slice_flow, flow_path)
                            current_slice_flow, flow_path = self.open_slice_video(flow_file, info, index*batch_size//info["fps"], face_locations[0])
                            write_frame_nums = 0
                        last_success_frame = frames[-1]
                        last_success_frame_index = index * batch_size + len(frames) - 1
                        self.write_slice_video(final_frames, current_slice_flow)
                        write_frame_nums += len(final_frames)
                        match_num += batch_size
                    now_schedule = index*batch_size*100//info["length"]
                    if now_schedule - last_schedule > 1:
                        self.log.log("start_fuzzy_job", "schedule: %d%% [%s/%s]" %(now_schedule, self.trans_seconds_to_time(index*(batch_size)//info["fps"]), total_time))
                        last_schedule = now_schedule
                        self.update_schedule(flow_file, index*batch_size*100//info["length"], match_num)
                        #every 5 percent reorder faces by match num, most likely face are moving to the front
                        if now_schedule % 5 == 0: 
                            self.reorder_faces(face_hit_num)
                #remain
                if info["length"]%batch_size != 0 and is_done == False:
                    frames = self.load_frame(flow, info["length"]%batch_size)
                    if frames != []:
                        face_locations = fr.face_locations(frames[0])
                        if self.compare_face(frames[0], face_locations, info["width"], info["height"], face_hit_num) == True:
                            face_locations = fr.face_locations(frames[-1])
                            if self.compare_face(frames[-1], face_locations, info["width"], info["height"], face_hit_num) == True:
                                final_frame = self.process_frame(frames)
                                self.write_slice_video(final_frames, current_slice_flow)
                                match_num += info["length"]%batch_size
                self.log.log("start_fuzzy_job", "schedule: 100%")
                self.log.log("start_fuzzy_job", "finish processing video [%s]" %(flow_file))
                if current_slice_flow != None:
                    self.close_slice_video(current_slice_flow, flow_path)
                flow.release()
                self.update_schedule(flow_file, 100, match_num)
            except KeyboardInterrupt as e:
                self.log.log("start_fuzzy_job", "Exception abort: %s" %(str(e)))
                traceback.print_exc()
                if current_slice_flow != None:
                    self.close_slice_video(current_slice_flow, flow_path)
                if flow != None:
                    flow.release()
                self.update_schedule(flow_file, index*batch_size*100//info["length"], match_num)
                exit()
                
    def start_exact_job(self, mode, sample_rate):
        now_schedule = 0
        last_schedule = 0
        current_slice_flow = None
        flow = None
        index = 0
        flow_path = ""
        face_hit_num = [0] * len(self.pic_db)
        for flow_file, info in self.video_db.items():
            try:
                if info["schedule"] == 100:
                    continue
                self.log.log("start_exact_job", "start processing video [%s]" %(flow_file))
                total_time = self.trans_seconds_to_time(info["length"]//info["fps"])
                write_frame_nums = 0
                match_num = 0
                flow = cv2.VideoCapture(flow_file)
                if info["schedule"] != 0:
                    flow.set(cv2.CAP_PROP_POS_FRAMES, info["length"]*100//info["schedule"])
                    self.log.log("start_exact_job", "continue with schedule %d\n" %(info["schedule"]))
                last_success_frame = []
                last_success_frame_index = -1
                #batch
                for index in range(0, info["length"]//sample_rate):
                    frames = self.load_frame(flow, sample_rate)
                    #if the first frame matched, check the last frame
                    face_locations = fr.face_locations(frames[0])
                    if self.compare_face(frames[0], face_locations, info["width"], info["height"], face_hit_num) == True:
                        final_frames = self.process_frame(frames)
                        #if the same scene
                        if (index - last_success_frame_index == 1) or \
                            (self.compare_scene(last_success_frame, frames[0], self.default_scene_confidence) == True):
                            #write it right behind the last video
                            write_frame_nums += len(final_frames)
                        #else if different scene
                        else:
                            self.close_slice_video(current_slice_flow, flow_path)
                            current_slice_flow, flow_path = self.open_slice_video(flow_file, info, index//info["fps"], face_locations[0])
                            write_frame_nums = 0
                        last_success_frame = frames[-1]
                        last_success_frame_index = index + len(frames) - 1
                        self.write_slice_video(final_frames, current_slice_flow)
                        write_frame_nums += len(final_frames)
                        match_num += 1
                    now_schedule = index*100//info["length"]
                    if now_schedule - last_schedule > 1:
                        self.log.log("start_exact_job", "schedule: %d%% [%s/%s]" %(now_schedule, self.trans_seconds_to_time(index//info["fps"]), total_time))
                        last_schedule = now_schedule
                        self.update_schedule(flow_file, index*100//info["length"], match_num)
                        #every 5 percent reorder faces by match num, most likely face are moving to the front
                        if now_schedule % 5 == 0: 
                            self.reorder_faces(face_hit_num)
                if current_slice_flow != None:
                    self.close_slice_video(current_slice_flow, flow_path)
                flow.release()
                self.update_schedule(flow_file, 100, match_num)
            except KeyboardInterrupt as e:
                self.log.log("start_exact_job", "Exception abort: %s" %(str(e)))
                traceback.print_exc()
                if current_slice_flow != None:
                    self.close_slice_video(current_slice_flow, flow_path)
                if flow != None:
                    flow.release()
                self.update_schedule(flow_file, index*100//info["length"], match_num)
                self.get_job_result()
                exit()
                
    def start_test_job(self, mode, sample_rate):
        current_slice_flow = None
        flow = None
        index = 0
        flow_path = ""
        face_hit_num = [0] * len(self.pic_db)
        for flow_file, info in self.video_db.items():
            try:
                if info["schedule"] == 100:
                    continue
                now_schedule = 0
                last_schedule = 0
                self.log.log("start_test_job", "start processing video [%s]" %(flow_file))
                total_time = self.trans_seconds_to_time(info["length"]//info["fps"])
                write_frame_nums = 0
                match_num = 0
                flow = cv2.VideoCapture(flow_file)
                if info["schedule"] != 0:
                    flow.set(cv2.CAP_PROP_POS_FRAMES, info["length"]*info["schedule"]//100)
                    self.log.log("start_test_job", "continue with schedule %d\n" %(info["schedule"]))
                    seconds = info["length"]*info["schedule"]//100//info["fps"]
                else:
                    seconds = 0
                last_success_frame = []
                last_success_frame_index = -1
                #batch
                total_seconds = info["length"]//info["fps"]
                while seconds < total_seconds:
                    frames = self.load_frame(flow, info["fps"])
                    if frames == []:
                        break
                    #if the first frame matched, look ahead for same scene
                    face_locations = fr.face_locations(frames[0])
                    if self.compare_face(frames[0], face_locations, info["width"], info["height"], face_hit_num) == True:
                        need_write = [frames[0]]
                        ahead_append_nums = 1
                        current_frame = frames[0]
                        last_success_frame = current_frame
                        done = False
                        for i in range(1, info["fps"]):
                            if self.compare_scene(last_success_frame, frames[i], self.default_scene_confidence) == True:
                                need_write.append(frames[i])
                                ahead_append_nums += 1
                                last_success_frame = frames[i]
                            else:
                                done = True
                                break
                        if done != True:
                            while True:
                                frames = self.load_frame(flow, 1)
                                if frames == []:
                                    break
                                if self.compare_scene(last_success_frame, frames[0], self.default_scene_confidence) == True:
                                    need_write.append(frames[0])
                                    ahead_append_nums += 1
                                    last_success_frame = frames[0]
                                else:
                                    break
                        #look before for same scene
                        last_success_frame = current_frame
                        done = False
                        seconds_tmp = seconds
                        while seconds_tmp != 0:
                            flow.set(cv2.CAP_PROP_POS_FRAMES, (seconds_tmp - 1)* info["fps"])
                            frames = self.load_frame(flow, info["fps"])
                            for j in range(len(frames)-1, -1, -1):
                                if self.compare_scene(last_success_frame, frames[j], self.default_scene_confidence) == True:
                                    need_write.insert(0, frames[j])
                                    last_success_frame = frames[j]
                                else:
                                    done = True
                                    break
                            if done == True:
                                break
                            seconds_tmp -= 1
                        final_frames = self.process_frame(need_write)
                        current_slice_flow, flow_path = self.open_slice_video(flow_file, info, seconds, face_locations[0])
                        self.write_slice_video(final_frames, current_slice_flow)
                        self.close_slice_video(current_slice_flow, flow_path)
                        seconds = (seconds+(ahead_append_nums+1)//info["fps"]+1)
                        flow.set(cv2.CAP_PROP_POS_FRAMES, seconds*info["fps"])
                        match_num += len(final_frames)
                    else:
                        seconds += 1
                    now_schedule = seconds*100//total_seconds
                    if now_schedule - last_schedule > 1:
                        self.log.log("start_test_job", "schedule: %d%% [%s/%s]" %(now_schedule, self.trans_seconds_to_time(seconds), total_time))
                        last_schedule = now_schedule
                        self.update_schedule(flow_file, now_schedule, match_num)
                        #every 5 percent reorder faces by match num, most likely face are moving to the front
                        if now_schedule % 5 == 0: 
                            self.reorder_faces(face_hit_num)
                flow.release()
                self.update_schedule(flow_file, 100, match_num)
            except KeyboardInterrupt as e:
                self.log.log("start_exact_job", "Exception abort: %s" %(str(e)))
                traceback.print_exc()
                if current_slice_flow != None:
                    self.close_slice_video(current_slice_flow, flow_path)
                if flow != None:
                    flow.release()
                self.update_schedule(flow_file, index*100//info["length"], match_num)
                self.get_job_result()
                exit()

    def recognize_aragaki(self, commands):
        self.log.log("recognize_aragaki", "your commands are %s" %(str(commands)))
        self.init_picture_database()
        self.init_video_database()
        self.init_slice_database()
        self.check_new_video()
        self.save_video_database()
        self.recexp.load_recognizer()
        if commands["mode"] == "fuzzy" or commands["mode"] == "fastest":
            self.start_fuzzy_job(commands["mode"], commands["sample-rate"])
        elif commands["mode"] == "exact":
            self.start_exact_job(commands["mode"], commands["sample-rate"])
        elif commands["mode"] == "test":
            self.start_test_job(commands["mode"], commands["sample-rate"])
        self.get_job_result()
        self.save_video_database()
        self.save_slice_database()
        
    def get_movie_slices_total_length(self):
        self.init_slice_database()
        total_length = 0
        for info in self.slice_db.values():
            total_length += (info["length"]//info["fps"])
        return total_length
        
    def get_movie_express_slices_length(self, express):
        self.init_slice_database()
        total_length = 0
        if express == "default":
            return self.get_movie_slices_total_length()
        for info in self.slice_db.values():
            if info["express"] == express:
                total_length += (info["length"]//info["fps"])
        return total_length
    
    def get_movie_slice_base_info(self):
        self.init_slice_database()
        min_pixel = 3440*1920
        return_info = None
        for info in self.slice_db.values():
            current_pixel = info["width"] * info["height"]
            if current_pixel < min_pixel:
                min_pixel = current_pixel
                return_info = info
        return return_info
        
        