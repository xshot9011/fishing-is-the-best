# import state
import os
import time
from numpy.lib.type_check import imag
import tensorflow.keras
import numpy as np
import cv2
import win32gui
import win32con
import win32ui
import ctypes
from PIL import Image, ImageOps, ImageGrab
from win32api import GetSystemMetrics
from get_image import ScreenCapture
import subprocess

# prerequisite

root_path = os.getcwd()
model_folder = os.path.join(root_path, 'model')
model_path = os.path.join(model_folder, 'keras_model.h5')
WINDOW_NAME = 'NoxPlayer'

## lib settings
np.set_printoptions(suppress=True)
ctypes.windll.user32.SetProcessDPIAware()


# global var

## pc information
width = GetSystemMetrics(0)
height = GetSystemMetrics(1)

## program
model = None
labels = {
    0: 'waiting',
    1: 'processing',
    2: 'done'
}
size = (224, 224)
prev_state = 0
now_state = 0

# function

def load_model(model_path):
    return tensorflow.keras.models.load_model(model_path)

def prepare_image(image):
    global size

    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    image = ImageOps.fit(image, size, Image.ANTIALIAS)
    image_array = np.asarray(image)
    normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
    data[0] = normalized_image_array
    return data

def get_class(data):
    global model
    prediction = model.predict(data)[0]
    return prediction.argmax(axis=-1)

def done():
    time.sleep(0.045)  # need tuning
    subprocess.call(['adb', 'shell', 'input', 'tap', '1350', '700'])
    time.sleep(1)

def fishing():
    os.system('adb shell input tap 1350 700')
    time.sleep(0.5)

if __name__ == "__main__":
    if model is None:
        model = load_model(model_path)

    done_lock = False
    fishing_lock = False
    start_time = time.time()

    while True:
        game_screen = ScreenCapture('NoxPlayer')
        game_screen.capture()

        if game_screen.image is not None:
            img = game_screen.get_crop_image()  
            img = cv2.resize(img, (224, 224), interpolation=cv2.INTER_AREA)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            img = np.asarray(img)
            normalized_image_array = (img.astype(np.float32) / 127.0) - 1
            normalized_image_array = np.expand_dims(normalized_image_array, axis=0)
            cv2.imshow('Bot_Ragnarok', img)

            now_state = get_class(normalized_image_array)
            print(labels[now_state])

            if labels[now_state] == 'done' and fishing_lock:
                print('Done state')
                done()
                fishing_lock = False
                continue
            if labels[now_state] == 'waiting' and not fishing_lock:
                print('Waiting state')
                fishing()
                fishing_lock = True
                continue

        if cv2.waitKey(1) == ord('q'):
            break
        # print("FPS: {}".format(1/(time.time()-start_time)))
        start_time = time.time()


# wait | proc -> proc -> wait -> done -> proc
# 0 | 1       -> 1    -> 0    -> 2    -> 1
