import cv2
import os
import face_recognition as fr
import numpy as np
import copy
from utils import *
import time
from any2jpg import any2jpg
import shutil

class RecExp():
    def __init__(self, log):
        self.log = log
        self.workarea = "./wa/"
        self.train_folder = self.workarea + "exp_train/"
        #data_db = {file_name : {gray, label}}
        self.data_db = None
        self.data_db_path = self.workarea + "training_data.pkl"
        self.recognizer = None
        self.recognizer_db_path = self.workarea + "recognizer.yml"
        self.label_define = ("default", "happy", "blue", "normal")
        self.predict_sample = 10
        
    def detect_face(self, img_file):
        image = fr.load_image_file(self.train_folder + img_file)
        face_locations = fr.face_locations(image)
        if len(face_locations) != 1:
            return []
        (top, right, bottom, left) = face_locations[0]
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return gray[top:bottom, left:right]
        
    def detect_flow_face(self, flow, index):
        flow.set(cv2.CAP_PROP_POS_FRAMES, index)
        ret, image = flow.read()
        face_locations = fr.face_locations(image[:, :, ::-1])
        if len(face_locations) != 1:
            return []
        (top, right, bottom, left) = face_locations[0]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return gray[top:bottom, left:right]
        
    def detect_image_face(self, image):
        face_locations = fr.face_locations(image[:, :, ::-1])
        if len(face_locations) != 1:
            return []
        (top, right, bottom, left) = face_locations[0]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return gray[top:bottom, left:right]
        
    def load_recognizer(self):
        if self.recognizer != None:
            return
        if os.path.exists(self.recognizer_db_path) == False:
            self.log.log("load_recognizer", "no recognizer found, create new recognizer")
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        else:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.recognizer.read(self.recognizer_db_path)
            self.log.log("load_recognizer", "found recognizer, going to use it")
    
    def save_recognizer(self):
        if self.recognizer != None:
            self.recognizer.write(self.recognizer_db_path)
    
    def load_traing_data(self):
        if self.data_db != None:
            return
        if os.path.exists(self.data_db_path) == False:
            self.log.log("load_traing_data", "no data_db found, use new db")
            self.data_db = dict()
        else:
            self.data_db = load_pkl(self.data_db_path)
            if self.data_db == None:
                self.log.log("load_traing_data", "data_db is empty, use new db")
                self.data_db = dict()
            else:
                self.log.log("load_traing_data", "found data_db, going to use it")
                
    def save_traing_data(self):
        save_pkl(self.data_db_path, self.data_db)
        
    def prepare_training_data(self):
        new_file = []
        for pic in os.listdir(self.train_folder):
            if pic not in self.data_db.keys():
                if "happy" in pic:
                    label = 1
                elif "blue" in pic:
                    label = 2
                else:
                    label = 3
                face = self.detect_face(pic)
                if face != []:
                    self.data_db[pic] = dict()
                    self.data_db[pic]["gray"] = copy.deepcopy(face)
                    self.data_db[pic]["label"] = label
                    new_file.append(pic)
        if new_file != []:
            self.log.log("prepare_training_data", "successfully loaded %d images" %(len(new_file)))
            self.log.log("prepare_training_data", "they are [" + " ".join(new_file) + "]")
                    
    def training(self):
        self.log.log("training", "training...")
        self.load_recognizer()
        self.load_traing_data()
        self.prepare_training_data()
        self.save_traing_data()
        if len(self.data_db) == 0:
            self.log.log("training", "training data is not prepared, please put some training data into [%s] first" %(self.train_folder))
            return
        faces = []
        labels = []
        for data in self.data_db.values():
            faces.append(data["gray"])
            labels.append(data["label"])
        self.recognizer.train(faces, np.array(labels))
        self.log.log("training", "training end successfully")
        self.save_recognizer()
        
    def predict_flow(self, flow, length):
        if self.recognizer == None:
            self.log.log("predict_flow", "recognizer is not initialized")
            return "default"
        if length < self.predict_sample:
            sample_step = 1
        else:
            sample_step = length//self.predict_sample
        result = [0,0,0,0]
        for i in range(0, length, sample_step):
            face = self.detect_flow_face(flow, i)
            if face != []:
                express_index, confidence = self.recognizer.predict(face)
                result[express_index] += 1
        self.log.log("predict_flow", "recognizer think it is a flow with %s face" %(self.label_define[result.index(max(result))]))
        return self.label_define[result.index(max(result))]
        
    def predict_image(self, image):
        if self.recognizer == None:
            self.log.log("predict_image", "recognizer is not initialized")
            return "default"
        face = self.detect_image_face(image)
        if face == []:
            self.log.log("predict_image", "face detected failed")
            return None
        express_index, confidence = self.recognizer.predict(face)
        self.log.log("predict_image", "recognizer think it is a image with %s face" %(self.label_define[express_index]))
        return self.label_define[express_index]
        
    def load_pic_from_folder(self, folder, max_num):
        valid_pic = []
        for pic in os.listdir(folder):
            if self.data_db != None and pic in self.data_db.keys():
                continue
            already_marked = False
            for express in self.label_define:
                if express in pic:
                    already_marked = True
                    break
            if already_marked == True:
                continue
            new_file_path = ".".join(pic.split(".")[:-1]) + ".jpg"
            any2jpg(folder + pic, folder + new_file_path)
            if self.detect_face(new_file_path) != []:
                valid_pic.append(folder + new_file_path)
                if max_num != 0 and len(valid_pic) >= max_num:
                    break
        if valid_pic != []:
            self.log.log("load_pic_from_folder", "successfully loaded %d images" %(len(valid_pic)))
            self.log.log("load_pic_from_folder", "they are [" + " ".join(valid_pic) + "]")
        return valid_pic
        
    def show_image_and_let_human_choose(self, pic):
        express = 0
        image = cv2.imread(pic)
        height = image.shape[0]
        width = image.shape[1]
        image_tmp = image.copy()
        text1 = "press 1: happy"
        text2 = "press 2: blue"
        text3 = "press 3: normal"
        cv2.putText(image_tmp, text1, (width//2,height//7*4), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image_tmp, text2, (width//2,height//7*5), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image_tmp, text3, (width//2,height//7*6), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)
        cv2.imshow(pic,image_tmp)
        k = cv2.waitKey(0)
        if k == ord('1'):
            express = 1
        elif k == ord('2'):
            express = 2
        elif k == ord('3'):
            express = 3
        cv2.destroyAllWindows()
        return express

    def store_image_as_training_data(self, pic, time_stamp, express, num):
        file_name = pic.split("/")[-1]
        path_name = '/'.join(pic.split("/")[:-1]) + '/'
        new_file_name = '.'.join(file_name.split('.')[:-1])
        suffix = file_name.split('.')[-1]
        new_file_name += '_'.join([time_stamp, self.label_define[express], str(num)]) + '.' + suffix
        save_name = self.train_folder + "/" + new_file_name
        shutil.copyfile(pic, save_name)
        if self.train_folder == path_name:
            os.remove(pic)
        
    def help_marking(self, commands, picture_path):
        self.load_traing_data()
        if commands["use-learn-pic"] == True:
            pics = self.load_pic_from_folder(picture_path, commands["max-pic-num"])
        else:
            pics = self.load_pic_from_folder(self.train_folder, commands["max-pic-num"])
        express_nums = [0,0,0,0]
        time_stamp = str(int(time.time()))
        for pic in pics:
            express = self.show_image_and_let_human_choose(pic)
            express_nums[express] += 1
            self.store_image_as_training_data(pic, time_stamp, express, express_nums[express])
        self.log.log("help_marking", "operation done on %d files" %(len(pics)))
    