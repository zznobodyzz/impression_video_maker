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
        image = fr.load_image_file(img_file)
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
            return [], []
        (top, right, bottom, left) = face_locations[0]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image, gray[top:bottom, left:right]
        
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
                    
    def training(self):
        self.log.log("training", "training...")
        self.load_recognizer()
        self.load_traing_data()
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
            face, gray = self.detect_flow_face(flow, i)
            if gray != []:
                express_index, confidence = self.recognizer.predict(gray)
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
        
    def manual_mark_image(self, name, image):
        height = image.shape[0]
        width = image.shape[1]
        image_tmp = image.copy()
        text0 = "press 0: gakki-smile"
        text1 = "press 1: default"
        text2 = "press 2: again"
        text3 = "press 3: last-slice"
        text4 = "press 4: end"
        cv2.putText(image_tmp, text0, (width//2,height//8*3), cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(image_tmp, text1, (width//2,height//8*4), cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(image_tmp, text2, (width//2,height//8*5), cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(image_tmp, text3, (width//2,height//8*6), cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(image_tmp, text4, (width//2,height//8*7), cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 255, 255), 2)
        while True:
            cv2.imshow(name, image_tmp)
            k = cv2.waitKey(0)
            cv2.destroyAllWindows()
            if k == ord('0'):
                return "gakki-smile"
            elif k == ord('1'):
                return "default"
            elif k == ord('2'):
                return "again"
            elif k == ord('3'):
                return "last-slice"
            elif k == ord('4'):
                return "end"
            else:
                continue
        
    def load_pic_from_slice(self, slice_folder, max_num):
        if slice_folder[-1] != '/':
            slice_folder += '/'
        success_num = 0
        valid_slice = []
        slices = os.listdir(self.workarea + slice_folder)
        while success_num < max_num:
            index = get_random_i(0, len(slices) - 1)
            slice_name = self.workarea + slice_folder + slices[index]
            if slice_name in self.data_db.keys():
                continue
            flow = cv2.VideoCapture(slice_name)
            frame, gray = self.detect_flow_face(flow, 0)
            if gray == []:
                flow.release()
                continue
            express = self.show_image_and_let_human_choose(None, frame)
            self.data_db[slice_name] = dict()
            self.data_db[slice_name]["type"] = "slice"
            self.data_db[slice_name]["gray"] = copy.deepcopy(gray)
            self.data_db[slice_name]["label"] = express
            success_num += 1
            valid_slice.append(slice_name)
        if valid_slice != []:
            self.log.log("load_pic_from_slice", "successfully loaded %d slices" %(len(valid_slice)))
            self.log.log("load_pic_from_slice", "they are [" + " ".join(valid_slice) + "]")
        return
       
    def load_pic_from_folder(self, folder, max_num):
        valid_pic = []
        success_num = 0
        for pic in os.listdir(folder):
            if pic in self.data_db.keys():
                continue
            new_file_path = ".".join(pic.split(".")[:-1]) + ".jpg"
            any2jpg(folder + pic, folder + new_file_path)
            pic = folder + new_file_path
            gray = self.detect_face(pic)
            if gray == []:
                continue
            express = show_image_and_let_human_choose(folder + new_file_path, None)
            self.data_db[pic] = dict()
            self.data_db[pic]["type"] = "picture"
            self.data_db[pic]["gray"] = copy.deepcopy(gray)
            self.data_db[pic]["label"] = express
            success_num += 1
            valid_pic.append(pic)
            if max_num == success_num:
                break
        if valid_pic != []:
            self.log.log("load_pic_from_folder", "successfully loaded %d images" %(len(valid_pic)))
            self.log.log("load_pic_from_folder", "they are [" + " ".join(valid_pic) + "]")
        return
        
    def show_image_and_let_human_choose(self, pic_file, pic_frame):
        express = 0
        if pic_file != None:
            image = cv2.imread(pic)
        else:
            image = pic_frame
        height = image.shape[0]
        width = image.shape[1]
        image_tmp = image.copy()
        text1 = "press 1: happy"
        text2 = "press 2: blue"
        text3 = "press 3: normal"
        cv2.putText(image_tmp, text1, (width//2,height//7*4), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image_tmp, text2, (width//2,height//7*5), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image_tmp, text3, (width//2,height//7*6), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)
        while True:
            cv2.imshow("show_image",image_tmp)
            k = cv2.waitKey(0)
            cv2.destroyAllWindows()
            if k == ord('1'):
                return 1
            elif k == ord('2'):
                return 2
            elif k == ord('3'):
                return 3
            else:
                continue
        
    def help_marking(self, commands, picture_path):
        self.load_traing_data()
        express_nums = [0,0,0,0]
        if commands["use-slice"] != None:
            self.load_pic_from_slice(commands["use-slice"], 50 if commands["max-pic-num"] == 0 else commands["max-pic-num"])
        elif commands["use-learn-pic"] == True:
            self.load_pic_from_folder(picture_path, commands["max-pic-num"])
        else:
            self.load_pic_from_folder(self.train_folder, commands["max-pic-num"])
        self.save_traing_data()
    