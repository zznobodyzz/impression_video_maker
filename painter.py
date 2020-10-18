import copy
from moviepy.editor import *
from moviepy.audio.fx import *
from utils import *
import cv2
from PIL import Image, ImageFont, ImageDraw
import json
import numpy as np
import codecs
import requests
import math
import face_recognition as fr

class OPED_Painter():
    def __init__(self, workarea, output_movie_path, material_path, \
                    font_type_path, default_wdco, default_bgco, \
                    opening_seconds, ending_seconds, log):
        self.workarea = workarea
        self.output_movie_path = output_movie_path
        self.material_path = material_path
        self.font_type_path = font_type_path
        self.opening_seconds = opening_seconds
        self.ending_seconds = ending_seconds
        self.default_wdco = default_wdco
        self.default_bgco = default_bgco
        self.log = log
        self.last_location = None
        self.last_vlog_convert = [None, None]
        self.vlog_start_funcs = [None, self.vlog_start1, self.vlog_start2, self.vlog_start3, self.vlog_start4, self.vlog_start5, self.vlog_start6]
        self.vlog_end_funcs = [None, self.vlog_end1, self.vlog_end2, self.vlog_end3, self.vlog_end4, self.vlog_end5, self.vlog_end6]
        self.vlog_config_funcs = [None, self.vlog_config1, self.vlog_config2, self.vlog_config3, self.vlog_config4, self.vlog_config5, self.vlog_config6]
        
    def paint_text(self, image, text, pos, text_rgb, size, font):
        font_obj = ImageFont.truetype(font, size)
        img_pil = Image.fromarray(image)
        draw = ImageDraw.Draw(img_pil)
        draw.text(pos, text, text_rgb, font_obj)
        image = np.array(img_pil)
        return image
        
    def decode_color_string(self, rgb_str):
        rgb_str = rgb_str.strip('[').strip(']')
        try:
            rgb = tuple([int(i) for i in rgb_str.split(',')])
            return rgb
        except Exception as e:
            #self.log.log("error", "rgb color format is not right")
            return None
        
    def generate_image(self, json_file, width, height):
        if os.path.exists(self.material_path + json_file) == True:
            with codecs.open(self.material_path + json_file, 'r', 'utf-8') as f:
                try:
                    text_info = json.load(f)
                except Exception as e:
                    self.log.log("generate_image", "broken json file [%s]" %(json_file))
                    return []
        else:
            self.log.log("generate_image", "[%s] not found in folder [%s]" %(json_file, self.material_path))
            return []
        if "text" not in text_info.keys():
            self.log.log("generate_image", "illegal text file [%s], missing text" %(self.material_path + json_file))
            return []
        if isinstance(text_info["text"], list) == False:
            self.log.log("generate_image", "illegal text file [%s], missing text" %(self.material_path + json_file))
            return []
        if "backgroundcolor" in text_info.keys():
            background_color = text_info["backgroundcolor"]
        else:
            background_color = self.default_bgco
        bg_rgb = self.decode_color_string(background_color)
        bg = np.ones((height, width, 3), dtype=np.uint8)
        #rgb type
        bg[:,:,0] = bg_rgb[0]
        bg[:,:,1] = bg_rgb[1]
        bg[:,:,2] = bg_rgb[2]
        if bg_rgb == None:
            self.log.log("generate_image", "illegal rgb backgroundcolor format %s" %(background_color))
            return []
        for content_info in text_info["text"]:
            if "content" not in content_info.keys():
                self.log.log("generate_image", "cotent not specified")
                return []
            content = content_info["content"]
            if "font" not in content_info.keys():
                font = self.font_type_path + "default.ttc"
            else:
                font = self.font_type_path + content_info["font"]
            if "color" in content_info.keys():
                textcolor = content_info["color"]
            else:
                textcolor = self.default_wdco
            text_rgb = self.decode_color_string(textcolor)
            if text_rgb == None:
                self.log.log("generate_image", "illegal rgb textcolor format %s" %(textcolor))
                return []
            if "top" in content_info.keys():
                top_pos = int(float(content_info["top"]) * height)
            else:
                top_pos = self.default_top_pos
            if "left" in content_info.keys():
                left_pos = int(float(content_info["left"]) * width)
            else:
                left_pos = self.default_left_pos
            if "size" in content_info.keys():
                size = int(content_info["size"])
            else:
                size = int(height/5*3*0.1)
            bg = self.paint_text(bg, content, (left_pos, top_pos), text_rgb, size, font)
        return bg
        
    def add_opening_or_ending(self, file_sub_name, out_movie_path, image, fps, codec, width, height):
        file_name = '.'.join(out_movie_path.split(".")[:-1]) + "_" + file_sub_name + "." + out_movie_path.split(".")[-1]
        output_flow = cv2.VideoWriter(file_name, codec, fps, (width, height))
        seconds = self.opening_seconds if file_sub_name == "opening" else self.ending_seconds
        for i in range(seconds * fps):
            output_flow.write(image)
        output_flow.release()
        movie = VideoFileClip(file_name)
        movie = movie.fadein(2, (1, 1, 1))
        movie = movie.fadeout(2, (1, 1, 1))
        return movie, file_name
        
    def get_random_material(self, kind, method):
        choosed = []
        if os.path.exists(self.material_path) == True:
            for file in os.listdir(self.material_path):
                if kind == 'json' and '.json' in file:
                    with codecs.open(self.material_path+file, "rb", 'utf-8') as f:
                        try:
                            text_info = json.load(f)
                            if text_info.has_key("method"):
                                if text_info["method"] == name:
                                    choosed.append(file)
                        except Exception as e:
                            self.log.log("get_random_material", "broken json file [%s]" %(text_file))
                            continue
                if kind == 'jpg' and '.jpg' in file:
                    choosed.append(file)
        if choosed == []:
            return None
        index = get_random_i(0,len(choosed)-1)
        return choosed[index]
        
    def get_random_opwd(self):
        return self.get_random_material("json", "opening")
        
    def get_random_edwd(self):
        return self.get_random_material("json", "ending")
        
    def get_random_gr(self):
        return self.get_random_material("jpg", None)
        
    def get_lrc(self, id):
        url = 'http://music.163.com/api/song/media?id=' + id
        data = None
        try:
            web_data = requests.get(url)
            return json.loads(web_data.text)
        except Exception as e:
            print(e)
            return None
        
    def generate_lrc_image(self, lrc, color, size, font):
        bg = np.ones((size+10, len(lrc) * size, 3), dtype=np.uint8)
        bg[:,:,:]=0
        return self.paint_text(bg, lrc, (0,0), color, size, font)
        
    def cover_lrc_image_to_bg(self, image, lrc_image, start_pos, end_pos):
        lrc_image = lrc_image[:, :end_pos[0],:]
        paint_index = np.where(np.all(lrc_image!=[0,0,0], axis = -1))
        image[paint_index] = lrc_image[paint_index]
        return image
        
    def paint_lrc(self, time_list, lrc_list, image, current_time, pos, color, size, font):
        lrc = ""
        time_index = 0
        for time in time_list:
            time_index = time_list.index(time)
            if current_time > time and current_time < time_list[time_index+1]:
                lrc = lrc_list[time_index]
                break
        if lrc == "" or time_index == len(time_list) - 1:
            return image
        lrc_graph = self.generate_lrc_image(lrc, color, size, self.font_type_path + font)
        total_width = len(lrc) * size
        cover_over_time = time_list[time_index + 1] - time_list[time_index]
        end_pos = round((current_time - time)/0.8/cover_over_time * total_width)
        if end_pos > total_width:
            end_pos = total_width
        return self.cover_lrc_image_to_bg(image, lrc_graph, pos, (end_pos, pos[1] + size+10))
    
    def get_lrc_json(self, json_file):
        file_path = self.material_path + json_file
        if os.path.exists(file_path) == False:
            self.log.log("get_lrc_json", "json file [%s] not found" %(json_file))
            return None
        with codecs.open(file_path, 'r', 'utf-8') as f:
            try:
                lrc_info = json.load(f)
            except Exception as e:
                self.log.log("get_lrc_json", "broken json file [%s]" %(json_file))
                return None
        if "id" not in lrc_info.keys():
            self.log.log("get_lrc_json", "song id not specified")
            return None
        if "top" not in lrc_info.keys():
            lrc_info["top"] = 20
        if "left" not in lrc_info.keys():
            lrc_info["left"] = 20
        if "size" not in lrc_info.keys():
            lrc_info["size"] = 30
        if "font" not in lrc_info.keys():
            lrc_info["font"] = "default.ttc"
        if "color" not in lrc_info.keys():
            lrc_info["color"] = (255,255,255)
        else:
            lrc_info["color"] = self.decode_color_string(lrc_info["color"])
        return lrc_info
        
    def paint_ghost(self, index, max_index, frame, fps):
        #use half seconds
        length = fps/2
        if max_index < length:
            return frame
        if max_index > fps:
            #start from half max index
            if (index >= (max_index/2)) and (index < (max_index/2+length)):
                index -= max_index/2
            else:
                self.last_location = None
                return frame
        else:
            #start frome begining
            if index > fps/2-1:
                self.last_location = None
                return frame
        alpha = 0.6 - index * (0.6/(length))
        if alpha < 0:
            return frame
        face_locations = fr.face_locations(frame[:,:,::-1], model = "cnn")
        if len(face_locations) == 0:
            if self.last_location == None:
                return frame
            top, right, bottom, left = self.last_location
        else:
            top, right, bottom, left = face_locations[0]
        overlay = frame.copy()
        times = (1.05 + (1 - alpha) * 0.2)
        resize_width = int(frame.shape[1] * times)
        resize_height = int(frame.shape[0] * times)
        center = (int((bottom - top) / 2 + top), int((right - left) / 2 + left))
        recenter = (int(center[0] * times), int(center[1] * times))
        overlay = cv2.resize(overlay, (resize_width, resize_height))
        move_height = int((recenter[0] - center[0])/2)
        move_width = int((recenter[1] - center[1])/2)
        overlay = overlay[move_height:resize_height - move_height, move_width:resize_width-move_width,:]
        overlay = cv2.resize(overlay, (frame.shape[1], frame.shape[0]))
        output = frame * (1.0 - alpha) + overlay * alpha
        for i in range(10,0,-1):
            alpha_tmp = alpha/10*(10-i)
            top_tmp = int(top/10*(10-i))
            bottom_tmp = int(frame.shape[0] - (frame.shape[0] - bottom) / 10 * (10-i))
            left_tmp = int(left/10*(10-i))
            right_tmp = int(frame.shape[1] - (frame.shape[1] - right) / 10 * (10-i))
            frame[top_tmp:bottom_tmp,left_tmp:right_tmp,:] = frame[top_tmp:bottom_tmp,left_tmp:right_tmp,:] * (1.0 - alpha_tmp) + overlay[top_tmp:bottom_tmp,left_tmp:right_tmp,:] * alpha_tmp
        output = output.astype(np.uint8)
        self.last_location = (top, right, bottom, left)
        return output
        
    def radial_blur(self, frame, blur):
        ori_width, ori_height = frame.shape[1], frame.shape[0]
        frame = cv2.copyMakeBorder(frame, 200, 200, 200, 200, cv2.BORDER_REFLECT)
        width, height = frame.shape[1], frame.shape[0]
        center_x = width / 2
        center_y = height / 2
        iterations = 5
        growMapx = np.tile(np.arange(width) + ((np.arange(width) - center_x)*blur), (height, 1)).astype(np.float32)
        shrinkMapx = np.tile(np.arange(width) - ((np.arange(width) - center_x)*blur), (height, 1)).astype(np.float32)
        growMapy = np.tile(np.arange(height) + ((np.arange(height) - center_y)*blur), (width, 1)).transpose().astype(np.float32)
        shrinkMapy = np.tile(np.arange(height) - ((np.arange(height) - center_y)*blur), (width, 1)).transpose().astype(np.float32)

        for i in range(iterations):
            tmp1 = cv2.remap(frame, growMapx, growMapy, cv2.INTER_LINEAR)
            tmp2 = cv2.remap(frame, shrinkMapx, shrinkMapy, cv2.INTER_LINEAR)
            frame = cv2.addWeighted(tmp1, 0.5, tmp2, 0.5, 0)
        frame = frame[200:ori_height+200,200:ori_width+200,:]
        return frame
    
    def motion_blur(self, frame, blur, angle):
        frame = np.array(frame)
        M = cv2.getRotationMatrix2D((blur / 2, blur / 2), angle, 1)
        motion_blur_kernel = np.diag(np.ones(blur))
        motion_blur_kernel = cv2.warpAffine(motion_blur_kernel, M, (blur, blur))
        motion_blur_kernel = motion_blur_kernel / blur
        blurred = cv2.filter2D(frame, -1, motion_blur_kernel)
        return blurred
        
    #shrink
    def vlog_convert1(self, frame, times, blur):
        origin_width = frame.shape[1]
        origin_height = frame.shape[0]
        resize_width = int(origin_width * times)
        resize_height = int(origin_height * times)
        fill_width = int((origin_width - resize_width) / 2)
        fill_height = int((origin_height - resize_height) / 2)
        overlay = cv2.resize(frame, (resize_width, resize_height))
        overlay = cv2.copyMakeBorder(overlay, fill_height, fill_height, fill_width, fill_width, cv2.BORDER_REFLECT)
        overlay = cv2.resize(overlay, (origin_width, origin_height))
        overlay = self.radial_blur(overlay, blur)
        return overlay
        
    def vlog_start1(self, index, max_index, frame, length):
        times = 0.5 + 0.5 / (length**2) * (index**2)
        blur = 0.05 - 0.04 / math.sqrt(length) * math.sqrt(index)
        return self.vlog_convert1(frame, times, blur)
    
    def vlog_end1(self, index, max_index, frame, length):
        times = 1 - 0.5 / math.sqrt(length) * math.sqrt(index - (max_index - length))
        blur = 0.01 + 0.04 / (length**2) * ((index - (max_index - length))**2)
        return self.vlog_convert1(frame, times, blur)
        
    def vlog_config1(self):
        self.convert_func_param = ["vlog1"]
        
    #90 degree spin
    def vlog_convert2(self, frame, angle, blur, direction):
        if direction != 'cw':
            angle = -angle
        origin_width = frame.shape[1]
        origin_height = frame.shape[0]
        center = (int(origin_width/2), int(origin_height/2))
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        overlay = cv2.warpAffine(frame, M, (origin_width, origin_height))
        cos = abs(math.cos(math.radians(angle)))
        sin = abs(math.sin(math.radians(angle)))
        resize_width = int(cos * origin_width + sin * origin_height)
        resize_height = int(sin * origin_width + cos * origin_height)
        times = resize_height/origin_height
        overlay = cv2.resize(overlay, (int(origin_width*times), resize_height))
        cut_width = int((overlay.shape[1] - origin_width) / 2)
        cut_height = int((overlay.shape[0] - origin_height) / 2)
        overlay = overlay[cut_height:cut_height + origin_height,cut_width:cut_width + origin_width,:]
        overlay = cv2.resize(overlay, (origin_width, origin_height))
        overlay = self.radial_blur(overlay, blur)
        return overlay
        
    def vlog_start2(self, index, max_index, frame, length):
        angle = 90 - 90 / math.sqrt(length) * math.sqrt(index)
        blur = 0.05 - 0.04 / math.sqrt(length) * math.sqrt(index)
        if self.convert_func_param != None and self.convert_func_param[0] == "vlog2":
            direction = self.convert_func_param[1]
        else:
            return frame
        return self.vlog_convert2(frame, angle, blur, direction)
            
    def vlog_end2(self, index, max_index, frame, length):
        angle = -(90 / (length**2) * ((index - (max_index - length)))**2)
        blur = 0.01 + 0.04 / (length**2) * ((index - (max_index - length))**2)
        return self.vlog_convert2(frame, angle, blur, self.convert_func_param[1])
        
    def vlog_config2(self):
        self.convert_func_param = ["vlog2", get_random_s(["cw","ucw"])]
        
    #enlarge
    def vlog_convert3(self, frame, times, blur):
        origin_width = frame.shape[1]
        origin_height = frame.shape[0]
        resize_width = int(origin_width * times)
        resize_height = int(origin_height * times)
        fill_width = int((resize_width - origin_width) / 2)
        fill_height = int((resize_height - origin_height) / 2)
        overlay = cv2.resize(frame, (resize_width, resize_height))
        overlay = overlay[fill_height:fill_height+origin_height,fill_width:fill_width+origin_width:]
        overlay = self.radial_blur(overlay, blur)
        return overlay
        
    def vlog_start3(self, index, max_index, frame, length):
        times = 1.5 - 0.5 / math.sqrt(length) * math.sqrt(index)
        blur = 0.05 - 0.04 / math.sqrt(length) * math.sqrt(index)
        return self.vlog_convert3(frame, times, blur)
    
    def vlog_end3(self, index, max_index, frame, length):
        times = 1 + 0.5 / (length**2) * ((index - (max_index - length))**2)
        blur = 0.01 + 0.04 / (length**2) * ((index - (max_index - length))**2)
        return self.vlog_convert3(frame, times, blur)
        
    def vlog_config3(self):
        self.convert_func_param = ["vlog3"]
        
    #45 degree spin
    def vlog_convert4(self, frame, angle, blur, corner, direction):
        origin_width = frame.shape[1]
        origin_height = frame.shape[0]
        if direction != 'cw':
           angle = -angle
        cos = abs(math.cos(math.radians(angle)))
        sin = abs(math.sin(math.radians(angle)))
        resize_width = int(cos * origin_width + sin * origin_height) + 200
        resize_height = int(sin * origin_width + cos * origin_height) + 200
        fill_width = resize_width - origin_width
        fill_height = resize_height - origin_height
        overlay = cv2.copyMakeBorder(frame, fill_height, fill_height, fill_width, fill_width, cv2.BORDER_REFLECT)
        if corner == 'lb':
            center = (fill_width,origin_height+fill_height)
        elif corner == 'rb':
            center = (fill_width+origin_width,origin_height+fill_height)
        elif corner == 'lt':
            center = (fill_width,fill_height)
        else:
            center = (fill_width+origin_width,fill_height)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        overlay = cv2.warpAffine(overlay, M, (resize_width, resize_height))
        overlay = overlay[fill_height:origin_height+fill_height,fill_width:origin_width+fill_width,:]
        overlay = self.motion_blur(overlay, blur, angle)
        return overlay
        
    def vlog_start4(self, index, max_index, frame, length):
        angle = 45 - 45 / math.sqrt(length) * math.sqrt(index)
        blur = int(80 - 79 / math.sqrt(length) * math.sqrt(index))
        if self.convert_func_param != None and self.convert_func_param[0] == "vlog4":
            corner, direction = self.convert_func_param[1], self.convert_func_param[2]
        else:
            return frame
        return self.vlog_convert4(frame, angle, blur, corner, direction)
    
    def vlog_end4(self, index, max_index, frame, length):
        angle = -(45 / (length**2) * ((index - (max_index - length)))**2)
        blur = int(1 + 79 / (length**2) * ((index - (max_index - length))**2))
        return self.vlog_convert4(frame, angle, blur, self.convert_func_param[1], self.convert_func_param[2])
        
    def vlog_config4(self):
        self.convert_func_param = ["vlog4", get_random_s(["lt","lb","rt","rb"]), get_random_s(["cw","ucw"])]
        
    def vlog_convert5(self, frame, offset, blur, angle, direction, spread):
        origin_width = frame.shape[1]
        origin_height = frame.shape[0]
        if angle == 45 or angle == -45:
            fill_width = int(offset / math.sqrt(2)/2)
            fill_height = int(offset / math.sqrt(2)/2)
            overlay = cv2.copyMakeBorder(frame, fill_height, fill_height, fill_width, fill_width, cv2.BORDER_REFLECT)
            if direction == "lt":
                if spread == False:
                    start_width1 = 0
                    start_width2 = overlay.shape[1] - origin_width
                    start_height1 = fill_height * 2
                    start_height2 = 0
                else:
                    start_width1 = fill_width * 2
                    start_width2 = overlay.shape[1] - origin_width - fill_width * 2
                    start_height1 = 0
                    start_height2 = overlay.shape[0] - origin_height
            else:
                if spread == False:
                    start_width1 = fill_width * 2
                    start_width2 = overlay.shape[1] - origin_width - fill_width * 2
                    start_height1 = 0
                    start_height2 = overlay.shape[0] - origin_height
                else:
                    start_width1 = 0
                    start_width2 = overlay.shape[1] - origin_width
                    start_height1 = fill_height * 2
                    start_height2 = 0
            overlay1 = np.array(overlay[start_height1:start_height1+origin_height, start_width1:start_width1+origin_width,:])
            overlay2 = np.array(overlay[start_height2:start_height2+origin_height, start_width2:start_width2+origin_width,:])
            for h in range(overlay1.shape[0]):
                for w in range(int((origin_width + origin_height) / 2 - h) + 1, overlay1.shape[1]):
                    overlay1[h, w] = overlay2[h, w]
            overlay = overlay1
        elif angle == 0:
            overlay = cv2.copyMakeBorder(frame, 0, 0, offset, offset, cv2.BORDER_REFLECT)
            if direction == "lt":
                start_width1 = offset * 2
                start_width2 = 0
            else:
                start_width1 = 0
                start_width2 = offset * 2
            if spread == True:
                tmp = start_width1
                start_width1 = start_width2
                start_width2 = tmp
            overlay1 = np.array(overlay[:int(origin_height/2), start_width1:start_width1+origin_width,:])
            overlay2 = np.array(overlay[int(origin_height/2):, start_width2:start_width2+origin_width,:])
            overlay = np.append(overlay1, overlay2, axis=0)
        else:
            overlay = cv2.copyMakeBorder(frame, offset, offset, 0, 0, cv2.BORDER_REFLECT)
            if direction == "lt":
                start_height1 = offset * 2
                start_height2 = 0
            else:
                start_height1 = 0
                start_height2 = offset * 2
            if spread == True:
                tmp = start_height1
                start_height1 = start_height2
                start_height2 = tmp
            overlay1 = np.array(overlay[start_height1:start_height1+origin_height,:int(origin_width/2),:])
            overlay2 = np.array(overlay[start_height2:start_height2+origin_height,int(origin_width/2):,:])
            overlay = np.append(overlay1, overlay2, axis=1)
        overlay = self.motion_blur(overlay, blur, 0)
        return overlay
        
    def vlog_start5(self, index, max_index, frame, length):
        blur = int(80 - 79 / math.sqrt(length) * math.sqrt(index))
        if self.convert_func_param != None and self.convert_func_param[0] == "vlog5":
            angle, direction = self.convert_func_param[1], self.convert_func_param[2]
        else:
            return frame
        if angle == 45 or angle == -45:
            max_offset = frame.shape[0] * math.sqrt(2) * 0.5
        elif angle == 0:
            max_offset = frame.shape[1] * 0.5
        else:
            max_offset = frame.shape[0] * 0.5
        offset = int(max_offset - max_offset / math.sqrt(length) * math.sqrt(index))
        return self.vlog_convert5(frame, offset, blur, angle, direction, False)
    
    def vlog_end5(self, index, max_index, frame, length):
        blur = int(1 + 79 / (length**2) * ((index - (max_index - length))**2))
        if self.convert_func_param[1] == 45 or self.convert_func_param[1] == -45:
            max_offset = frame.shape[0] * math.sqrt(2) * 0.5
        elif self.convert_func_param[1] == 0:
            max_offset = frame.shape[1] * 0.5
        else:
            max_offset = frame.shape[0] * 0.5
        offset = int(max_offset / (length**2) * ((index - (max_index - length)))**2)
        return self.vlog_convert5(frame, offset, blur, self.convert_func_param[1], self.convert_func_param[2], True)
        
    def vlog_config5(self):
        self.convert_func_param = ["vlog5", get_random_s([-45,45,0,90]), get_random_s(["lt","rb"])]
        
    def vlog_convert6(self, frame, offset, blur, direction, spread):
        origin_width = frame.shape[1]
        origin_height = frame.shape[0]
        if direction == "top" or direction == "bottom":
            overlay = cv2.copyMakeBorder(frame, offset, offset, 0, 0, cv2.BORDER_REFLECT)
            if spread == True:
                start_height = offset * 2
            else:
                start_height = 0
            overlay = np.array(overlay[start_height:start_height+origin_height, :, :])
        else:
            overlay = cv2.copyMakeBorder(frame, 0, 0, offset, offset, cv2.BORDER_REFLECT)
            if spread == True:
                start_width = offset * 2
            else:
                start_width = 0
            overlay = np.array(overlay[:, start_width:start_width+origin_width, :])
        overlay = self.motion_blur(overlay, blur, 0)
        return overlay
        
    def vlog_start6(self, index, max_index, frame, length):
        blur = int(80 - 79 / math.sqrt(length) * math.sqrt(index))
        if self.convert_func_param != None and self.convert_func_param[0] == "vlog6":
            direction = self.convert_func_param[1]
        else:
            return frame
        if direction == 'top' or direction == 'bottom':
            max_offset = frame.shape[0] * 0.5
        else:
            max_offset = frame.shape[1] * 0.5
        offset = int(max_offset - max_offset / math.sqrt(length) * math.sqrt(index))
        return self.vlog_convert6(frame, offset, blur, direction, False)
    
    def vlog_end6(self, index, max_index, frame, length):
        blur = int(1 + 79 / (length**2) * ((index - (max_index - length))**2))
        if self.convert_func_param[1] == 'top' or self.convert_func_param[1] == 'bottom':
            max_offset = frame.shape[0] * 0.5
        else:
            max_offset = frame.shape[1] * 0.5
        offset = int(max_offset / (length**2) * ((index - (max_index - length)))**2)
        return self.vlog_convert6(frame, offset, blur, self.convert_func_param[1], True)
        
    def vlog_config6(self):
        self.convert_func_param = ["vlog6", get_random_s(["top","bottom","left","right"])]
        
    def vlog_convert(self, index, max_index, frame, fps):
        length = int(fps/4)
        if max_index < length * 2:
            return frame
        if index <= length:
            if self.last_vlog_convert[0] != None:
                return self.last_vlog_convert[0](index, max_index, frame, length)
            return frame
        elif index == max_index - length:
            func_index = get_random_i(1,len(self.vlog_end_funcs)-1)
            self.vlog_config_funcs[func_index]()
            self.last_vlog_convert[0] = self.vlog_start_funcs[func_index]
            self.last_vlog_convert[1] = self.vlog_end_funcs[func_index]
            return self.vlog_end_funcs[func_index](index, max_index, frame, length)
        elif index > max_index - length:
            return self.last_vlog_convert[1](index, max_index, frame, length)
        else:
            return frame
        