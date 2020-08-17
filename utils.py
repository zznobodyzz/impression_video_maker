import random
import pickle
import copy
import cv2

def get_argv(argvs, index, default = None):
    if index + 1 < len(argvs):
        if argvs[index + 1].isdigit() == True:
            return int(argvs[index + 1])
        return argvs[index + 1]
    return default
    
def get_argvs(argvs, index, default = []):
    result = []
    if index + 1 == len(argvs):
        return default
    for i in range(index + 1, len(argvs) - 1):
        if argvs[i][0] == '-':
            break
        if argvs[i].isdigit() == True:
            result.append(int(argvs[i]))
        else:
            result.append(argvs[i])
    return result
    
def get_argvstr(argvs, index, default = []):
    if index + 1 < len(argvs):
        return argvs[index + 1]
    return default
    
def get_random_i(start, end):
    return random.randint(start, end)
    
def get_random_s(list):
    index = random.randint(0, len(list) - 1)
    return list[index]
    
def save_pkl(pkl_file_path, obj):
    with open(pkl_file_path, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_pkl(pkl_file_path):
    with open(pkl_file_path, 'rb') as f:
        return pickle.load(f)
        
        
def fuzzy_match_file_name(file_name, src_file):
    file_name = file_name.lower()
    file_tmp = copy.deepcopy(src_file)
    file_tmp = file_tmp.replace(" ", "")
    file_tmp = file_tmp.replace("-", "")
    file_tmp = file_tmp.lower()
    if file_name in file_tmp:
        return True
    return False

def append_file_name(file_name, append_name):
    return '.'.join(file_name.split('.')[:-1]) + append_name + '.' + file_name.split('.')[-1]
    
def show_image(title, image):
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()