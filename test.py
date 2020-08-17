'''
from painter import OPED_Painter
from log import Log
import numpy as np
import cv2
import datetime
import sys
import requests
p = OPED_Painter("./wa/", "./wa/output_movie/", "./wa/material/", "./wa/material/font/", "[255,255,255]", \
                            "[0,0,0]", 6, 4, Log())

g = np.ones((20, 140, 3), dtype=np.uint8)
r = p.paint_text(g, "aaaaaaa", (0,0), (255,255,255), 20, "./wa/material/font/default.ttc")
cv2.imshow("111", r)
cv2.waitKey(0)
cv2.destroyAllWindows()


a = p.get_lrc("432821964")
b = a["lyric"].split('\n')
time_list = []
lrc_list = []
for c in b:
    try:
        t = c[1:c.index(']')]
        m = int(t.split(':')[0])
        s = float(t.split(':')[1])
        time_list.append(m*60 + s)
        lrc_list.append(c[c.index(']')+1:])
    except Exception as e:
        continue
end_time = 500.0
time_list.append(end_time)
lrc_list.append("")
g = np.ones((1080, 1920, 3), dtype=np.uint8)
output = cv2.VideoWriter("test.avi", cv2.VideoWriter_fourcc(*'XVID'), 30, (1920,1080))
sc = 0
print("start:" + datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'))
for i in range(1000):
    g[:,:,:] = 40
    out = p.paint_lrc(time_list, lrc_list, g, i/30, (20,20), (255,255,255), 30, "maobi.ttc")
    output.write(out)
output.release()
print("end:  " + datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'))

'''
import librosa
import numpy as np

y, sr = librosa.load('hikoten.mp3')
# get onset envelope
onset_env = librosa.onset.onset_strength(y, sr=sr, aggregate=np.median)
# get tempo and beats
tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
# we assume 4/4 time
meter = 4
# calculate number of full measures 
measures = (len(beats) // meter)
# get onset strengths for the known beat positions
# Note: this is somewhat naive, as the main strength may be *around*
#       rather than *on* the detected beat position. 
beat_strengths = onset_env[beats]
# make sure we only consider full measures
# and convert to 2d array with indices for measure and beatpos
measure_beat_strengths = beat_strengths[:measures * meter].reshape(-1, meter)
# add up strengths per beat position
beat_pos_strength = np.sum(measure_beat_strengths, axis=0)
# find the beat position with max strength
downbeat_pos = np.argmax(beat_pos_strength)
# convert the beat positions to the same 2d measure format
full_measure_beats = beats[:measures * meter].reshape(-1, meter)
# and select the beat position we want: downbeat_pos
downbeat_frames = full_measure_beats[:, downbeat_pos]
print('Downbeat frames: {}'.format(downbeat_frames))
# print times
downbeat_times = librosa.frames_to_time(downbeat_frames, sr=sr)
print('Downbeat times in s: {}'.format(downbeat_times))