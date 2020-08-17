from PIL import Image
import cv2
import os
import shutil

def png2jpg(png_file_path, jpg_file_path):
    img = cv2.imread(png_file_path, 0)
    w, h = img.shape[::-1]
    outfile = jpg_file_path
    img = Image.open(png_file_path)
    img = img.resize((int(w / 2), int(h / 2)), Image.ANTIALIAS)
    if len(img.split()) == 4:
        # prevent IOError: cannot write mode RGBA as BMP
        r, g, b, a = img.split()
        img = Image.merge("RGB", (r, g, b))
        img.convert('RGB').save(jpg_file_path, quality=70)
    else:
        img.convert('RGB').save(jpg_file_path, quality=70)
    return True
        
def jpeg2jpg(jpeg_file_path, jpg_file_path):
    shutil.copyfile(jpeg_file_path, jpg_file_path)
    return True
        
def any2jpg(input_file_path, output_file_path):
    if os.path.exists(input_file_path) == False:
        return False
    if os.path.exists(output_file_path) == True:
        return True
    suffix = input_file_path.split(".")[-1]
    if suffix == "png":
        return png2jpg(input_file_path, output_file_path)
    if suffix == "jpeg":
        return jpeg2jpg(input_file_path, output_file_path)
    else:
        return True
    