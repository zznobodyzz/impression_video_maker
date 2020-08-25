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
        i = 0
        for h in range(start_pos[1], end_pos[1]):
            j = 0
            for w in range(start_pos[0], end_pos[0]):
                if (lrc_image[i][j] != [0,0,0]).all():
                    image[h][w] = lrc_image[i][j]
                j += 1
            i += 1
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
        
    def paint_ghost(self, index, frame):
        if index > 9:
            self.last_location = None
            return frame
        face_locations = fr.face_locations(frame[:,:,::-1], model = "cnn")
        if len(face_locations) == 0:
            if self.last_location == None:
                return frame
            top, right, bottom, left = self.last_location
        else:
            top, right, bottom, left = face_locations[0]
        alpha = 0.5 - (index + 1) * 0.05
        overlay = frame.copy()
        times = (1.05 + (1 - alpha) * 0.3)
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
        output = output.astype(np.uint8)
        self.last_location = (top, right, bottom, left)
        return output
        