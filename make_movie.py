import copy
from moviepy.editor import *
from moviepy.audio.fx import *
from utils import *
import cv2
from painter import OPED_Painter

class Mov():
    def __init__(self, log, rec, mus):
        self.log = log
        self.rec = rec
        self.mus = mus
        self.workarea = "./wa/"
        self.output_movie_path = self.workarea + "output_movie/"
        self.material_path = self.workarea + "material/"
        self.font_type_path = self.workarea + "material/font/"
        self.opening_seconds = 6
        self.ending_seconds = 4
        self.default_wdco = "[255,255,255]"
        self.default_bgco = "[0,0,0]"
        self.default_output_fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.default_moviepy_codec = None
        self.default_output_suffix = '.mp4'
        self.default_output_fps = 30
        self.painter = OPED_Painter(self.workarea, self.output_movie_path, self.material_path, \
                                    self.font_type_path, self.default_wdco, self.default_bgco, \
                                    self.opening_seconds, self.ending_seconds, self.log)
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
            self.rec.init_slice_database()
        express_slices = []
        for slice, slice_info in self.rec.slice_db.items():
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
                slice_size > slices_list[index][1]["length"]//slices_list[index][1]["fps"]:
                index = get_random_i(0, len(slices_list) - 1)
            return slices_list[index][0], slices_list[index][1]
        #make sure same slice won't be neighbour
        loop = 0
        while (slices_list[index][0] in already_choosen or \
                already_choosen[-1] == slices_list[index][0] or \
                frame_nums > slices_list[index][1]["length"] or \
                slice_size > slices_list[index][1]["length"]//slices_list[index][1]["fps"]) and \
                (loop < len(slices_list)):
            index = get_random_i(0, len(slices_list) - 1)
            loop += 1
        return slices_list[index][0], slices_list[index][1]
        
    def get_beats_by_rate(self, beats, rate):
        select_beats = []
        for i in range(0, len(beats), rate):
            select_beats.append(beats[i])
        return select_beats
        
    def write_frame_to_flow(self, flow, frame, width, height):
        if frame.shape[0] != height or frame.shape[1] != width:
            frame = cv2.resize(frame, (width, height))
        flow.write(frame)
        
    def calc_compensation(self, beats, fps, precise):
        compensation = [0] * len(beats)
        payback = 0
        for i in range(len(beats) - 1):
            base1 = fps * (beats[i+1] - beats[i])
            base2 = int(base1)
            payback += (base1 - base2)
        paybackf = round((len(beats) - 1)/payback, precise)
        i = 0
        while i < (len(beats) - 1):
            index = round(i * paybackf)
            if index > len(beats) - 1:
                break
            compensation[index] += 1
            i += 1
        return compensation
        
    def combine_slices_with_beats(self, beats, slices, beat_rate, output_file_name, time, caption_height):
        already_choosen = []
        base_slice_info = self.rec.get_movie_slice_base_info()
        writed_frames = 0
        real_height = base_slice_info["height"] - caption_height
        for i in range(len(beats)):
            beats[i] -= 0.2
        output_flow = cv2.VideoWriter(output_file_name, self.default_output_fourcc, self.default_output_fps, (base_slice_info["width"],real_height))
        time_up = False
        total_length = self.default_output_fps * time
        need_write_ahead = False
        compensation = self.calc_compensation(beats, self.default_output_fps, 5)
        for i in range(len(beats) - 1):
            beat_frame_nums = int(self.default_output_fps * (beats[i+1] - beats[i])) + compensation[i]
            '''
            if i == 0:
                slice_name = "./wa/slice_video/第10回.(Av27134146,P10)_648s.avi"
                for slice in slices:
                    if slice[0] == slice_name:
                        slice_info = slice[1]
                        print("1111")
                        break
            else:
            '''
            slice_name, slice_info = self.get_slice(slices, beat_frame_nums, 0, already_choosen)
            already_choosen.append(slice_name)
            slice_flow = cv2.VideoCapture(slice_name)
            for j in range(beat_frame_nums):
                ret, frame = slice_flow.read()
                if ret == False:
                    slice_flow.release()
                    slice_name, slice_info = self.get_slice(slices, beat_frame_nums - j, 0, already_choosen)
                    already_choosen.append(slice_name)
                    #less than half second, continue write
                    slice_flow = cv2.VideoCapture(slice_name)
                    ret, frame = slice_flow.read()
                if caption_height != 0:
                    frame = frame[:frame.shape[0]-caption_height,:,:]
                self.write_frame_to_flow(output_flow, frame, base_slice_info["width"], real_height)
                writed_frames += 1
                if writed_frames == total_length:
                    slice_flow.release()
                    time_up = True
                    break
            if time_up == True:
                break
            self.log.log("combine_slices_with_beats", "schedule: %d%%" %(i*100//len(beats)))
        self.log.log("combine_slices_with_beats", "schedule: 100%")
        output_flow.release()
        return base_slice_info["width"], real_height
        
    def combine_slices_without_beats(self, slices, slice_size, output_file_name, time, caption_height):
        already_choosen = []
        base_slice_info = self.rec.get_movie_slice_base_info()
        real_height = base_slice_info["height"] - caption_height
        writed_frames = 0
        output_flow = cv2.VideoWriter(output_file_name, self.default_output_fourcc, self.default_output_fps, (base_slice_info["width"],real_height))
        total_length = self.default_output_fps * time
        slice_name, slice_info = self.get_slice(slices, 0, slice_size, already_choosen)
        already_choosen.append(slice_name)
        slice_flow = cv2.VideoCapture(slice_name)
        schedule = 0
        last_schedule = 0
        i= 0
        while i < total_length:
            write_frame_nums = 0
            need_write_nums = (slice_size*self.default_output_fps) if (total_length - i > slice_size*self.default_output_fps) else (total_length - i)
            for j in range(need_write_nums):
                ret, frame = slice_flow.read()
                if ret == False:
                    break
                if caption_height != 0:
                    frame = frame[:frame.shape[0]-caption_height,:,:]
                self.write_frame_to_flow(output_flow, frame, base_slice_info["width"], real_height)
                write_frame_nums += 1
            slice_flow.release()
            slice_name, slice_info = self.get_slice(slices, 0, slice_size, already_choosen)
            already_choosen.append(slice_name)
            slice_flow = cv2.VideoCapture(slice_name)
            i += write_frame_nums
            schedule = i*100//total_length
            if schedule - last_schedule > 1:
                self.log.log("combine_slices_without_beats", "schedule: %d%%" %(schedule))
                last_schedule = schedule
        self.log.log("combine_slices_without_beats", "schedule: 100%")
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
        final = movie.set_audio(music).fadeout(2, (1, 1, 1))
        return final, final_file
        
    def add_lrc(self, song_id, movie_file, width, height):
        movie_flow = cv2.VideoCapture(movie_file)
        output_tmp_file = append_file_name(movie_file, "_lrc")
        output_flow = cv2.VideoWriter(output_tmp_file, int(movie_flow.get(cv2.CAP_PROP_FOURCC)), self.default_output_fps, (width,height))
        self.log.log("add_lrc", "adding lrc...")
        lrc_origin = self.painter.get_lrc(song_id)
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
            out = self.painter.paint_lrc(time_list, lrc_list, frame, i/self.default_output_fps, (20,20), (255,255,255), 35, "maobi.ttc")
            output_flow.write(out)
            schedule = int(i*100/length)
            if schedule - last_schedule > 1:
                self.log.log("add_lrc", "schedule: %d%%" %(schedule))
                last_schedule = schedule
        output_flow.release()
        return output_tmp_file
        
    def make(self, commands, music_file_list, music_info_list, beats, slices):
        movie_file = self.output_movie_path + commands["title"] + self.default_output_suffix
        if commands["beat-mode"] == True:
            width, height = self.combine_slices_with_beats(beats, slices, commands["beat-rate"], movie_file, commands["time"], commands["caption-height"])
        else:
            width, height = self.combine_slices_without_beats(slices, commands["slice-size"], movie_file, commands["time"], commands["caption-height"])
        if commands["lrc-id"] != "":
            lrc_movie_file = self.add_lrc(commands["lrc-id"], movie_file, width, height)
            os.remove(movie_file)
            movie_file = lrc_movie_file
        out_movie, out_movie_path = self.add_music(music_file_list, music_info_list, commands["time"], movie_file, self.output_movie_path + commands["title"])
        if commands["opconf"] == None and commands["edconf"] == None:
            os.remove(movie_file)
            return
        full_movie = []
        make_opening = False
        make_ending = False
        if commands["opconf"] != None:
            make_opening = True
            image = self.painter.generate_image(commands["opconf"], width, height)
            if image == []:
                return
            opening_movie, opening_file_name = self.painter.add_opening_or_ending("opening", out_movie_path, image, self.default_output_fps, self.default_output_fourcc, width, height)
            full_movie.append(opening_movie)
        full_movie.append(out_movie)
        if commands["edconf"] != None:
            make_ending = True
            image = self.painter.generate_image(commands["edconf"], width, height)
            if image == []:
                return
            ending_movie, ending_file_name = self.painter.add_opening_or_ending("ending", out_movie_path, image, self.default_output_fps, self.default_output_fourcc, width, height)
            full_movie.append(ending_movie)
        if len(full_movie) > 1:
            final_movie = concatenate_videoclips(full_movie, method='compose')
            final_path = '.'.join(out_movie_path.split('.')[:-1]) + \
                            ('_op' if make_opening == True else '') + \
                            ('_ed' if make_ending == True else '') + \
                            '.' + out_movie_path.split('.')[-1]
        else:
            final_movie = full_movie[0]
        final_movie.write_videofile(final_path, codec = self.default_moviepy_codec)
        if make_opening == True:
            os.remove(opening_file_name)
        if make_ending == True:
            os.remove(ending_file_name)
        os.remove(movie_file)
        
    def preprocess_music(self, commands, music_info):
        beats = []
        base_time = 0
        for info in music_info:
            info["beats"].insert(0, 0)
            step = 1
            '''
            if info["beat_delta"] < 1:
                for step in range(2, 5):
                    if info["beat_delta"] * step > 1:
                        break
            '''
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
            self.rec.init_slice_database()
        express_slices = []
        for slice, slice_info in self.rec.slice_db.items():
            if (slice_info["express"] == commands["express"] or commands["express"] == "default") and \
                (commands["feature"] == "" or commands["feature"] in slice) and \
                (slice_info["length"] > commands["slice-size"] * slice_info["fps"]):
                    express_slices.append([slice, slice_info])
        if express_slices == []:
            self.log.log("preprocess_slice", "no slices were picked")
        return express_slices
        
    def make_aragaki_movie(self, commands):
        self.log.log("make_aragaki_movie", "your commands are: %s" %(str(commands)))
        music_file, music_info, total_length = self.get_music(commands["music"])
        if music_info == []:
            return
        if commands["all-mode"] == True:
            commands["time"] = self.rec.get_movie_express_slices_length(commands["express"], rescan = False)
            self.all_mode = True
        if commands["no-repeat"] == True:
            self.no_repeat = True
        if commands["time"] == 0:
            self.log.log("make_aragaki_movie", "movie time length using music time length")
            commands["time"] = int(total_length)
        beats = self.preprocess_music(commands, music_info)
        slices = self.preprocess_slice(commands)
        if slices == []:
            return
        output_movie = self.make(commands, music_file, music_info, beats, slices)
        
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
                if self.rec.compare_scene(frame, last_frame, 15) == True:
                    write_frame_nums += 1
                elif write_frame_nums != 0:
                    new_slice_info = copy.deepcopy(slice[1])
                    new_slice_info["length"] = write_frame_nums
                    self.rec.update_slice_db(output_tmp_file, new_slice_info, predict = True)
                    output_flow.release()
                    sub_slice_num += 1
                    write_frame_nums = 0
                    output_tmp_file = append_file_name(slice[0], "_cutscenetmp%d" %(sub_slice_num))
                    self.log.log("cut_scene", "openging new output file [%s]" %(output_tmp_file))
                    output_flow = cv2.VideoWriter(output_tmp_file, slice[1]["fourcc"], slice[1]["fps"], (slice[1]["width"],slice[1]["height"]))
                output_flow.write(frame)
                last_frame = frame
            self.log.log("cut_scene", "[%s] cut successful" %(slice[0]))
            #self.rec.update_slice_db(slice[0], None, operation = "del", predict = True)
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
                self.rec.update_slice_db(output_tmp_file, new_slice_info, predict = True)
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
                self.rec.update_slice_db(output_tmp_file, new_slice_info, operation = "add", predict = True)
            output_flow.release()
            slice_flow.release()
            #self.rec.update_slice_db(slice[0], None, operation = "del", predict = False)
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
            #self.rec.update_slice_db(slice[0], slice[1])
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
    