# import module
import os
import time
import cv2
import win32gui
import win32ui
import win32con
import win32api
import ctypes
import numpy as np
import tensorflow.keras
from PIL import Image, ImageOps, ImageGrab

class ScreenCapture:
    __slots__ = [
        'window_name', 'hwnd', 'image', 'position', 'X_START_PROPORTION', 
        'Y_START_PROPORTION', 'X_FLAG_PROPORTION', 'Y_FLAG_PROPORTION'
    ]

    def __init__(self, window_name, image=None, position=[]):
        self.window_name = window_name
        self.image = image
        # position [left,top,right,bottom]
        self.position = position

        # constant initial
        self.X_START_PROPORTION = 0.75
        self.Y_START_PROPORTION = 0.625
        self.X_FLAG_PROPORTION = 0.15
        self.Y_FLAG_PROPORTION = 0.25

    def _set_position(self, hwnd):
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        self.position.append(left)
        self.position.append(top)
        self.position.append(right)
        self.position.append(bottom)

    def capture(self):
        # locate window
        self.hwnd = win32gui.FindWindow(None, self.window_name)
        if self.hwnd:
            # set window position
            self._set_position(self.hwnd)
            width = self.position[2] - self.position[0]
            height = self.position[3] - self.position[1]

            # try to crop border
            border_pixel = 0
            titlebar_pixel = 0
            width = width - (border_pixel * 2)
            height = height - (titlebar_pixel + (border_pixel))

            # Create BitMap for Screenshot
            wDC = win32gui.GetWindowDC(self.hwnd)
            dcObj=win32ui.CreateDCFromHandle(wDC)
            cDC=dcObj.CreateCompatibleDC()
            dataBitMap = win32ui.CreateBitmap()
            dataBitMap.CreateCompatibleBitmap(dcObj, width, height)
            cDC.SelectObject(dataBitMap)
            cDC.BitBlt((0,0),(width,height) , dcObj, (border_pixel,titlebar_pixel), win32con.SRCCOPY)

            # Save to sample file
            # dataBitMap.SaveBitmapFile(cDC, bmpfilenamename)
            signed_int_array = dataBitMap.GetBitmapBits(True)
            self.image = np.fromstring(signed_int_array, dtype='uint8')
            self.image.shape = (height, width, 4)

            # Free Resources
            dcObj.DeleteDC()
            cDC.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, wDC)
            win32gui.DeleteObject(dataBitMap.GetHandle())

            # return self.image

    def resize(self, scale_percent=60):
        if self.image is not None:
            width = int(self.image.shape[1] * scale_percent / 100)
            height = int(self.image.shape[0] * scale_percent / 100)
            dim = (width, height)
            # resize image
            return cv2.resize(self.image, dim, interpolation=cv2.INTER_AREA)
        return None

    def get_crop_image(self, X_START_PROPORTION=0.75, Y_START_PROPORTION=0.625, X_FLAG_PROPORTION=0.15, Y_FLAG_PROPORTION=0.25):
        if self.image is not None:
            width, height = self.image.shape[1], self.image.shape[0]
            x_start = int(X_START_PROPORTION*width)
            y_start = int(Y_START_PROPORTION*height)
            x_step = int(X_FLAG_PROPORTION*width)
            y_step = int(Y_FLAG_PROPORTION*height)
            return self.image[y_start:y_start+y_step, x_start:x_start+x_step]

    def click(self, msg=None):
        if msg is not None:
            print(msg)
        width, height = self.image.shape[1], self.image.shape[0]
        x_start = int(self.X_START_PROPORTION*width)
        y_start = int(self.Y_START_PROPORTION*height)
        x_step = int((self.X_FLAG_PROPORTION/2)*width)
        y_step = int((self.Y_FLAG_PROPORTION/2)*height)
        l_parameter = win32api.MAKELONG(x_start+x_step, y_start+y_step)
        
        win32gui.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_parameter)
        win32gui.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, None, l_parameter)

# prerequisite

root_path = os.getcwd()
model_folder = os.path.join(root_path, 'model')
model_path = os.path.join(model_folder, 'keras_model.h5')
WINDOW_NAME = 'NoxPlayer'

## lib settings
np.set_printoptions(suppress=True)
ctypes.windll.user32.SetProcessDPIAware()

# global var

## program
model = None
labels = {
    0: 'waiting',
    1: 'processing',
    2: 'done'
}
size = (224, 224)

# function

def load_model(model_path):
    return tensorflow.keras.models.load_model(model_path)

def get_class(data):
    global model
    prediction = model.predict(data)[0]
    return prediction.argmax(axis=-1)

if __name__ == "__main__":
    if model is None:
        model = load_model(model_path)

    done_lock = False
    fishing_lock = False
    start_time = time.time()

    while True:
        game_screen = ScreenCapture(WINDOW_NAME)
        game_screen.capture()

        if game_screen.image is not None:
            img = game_screen.get_crop_image()  
            img = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            img = np.asarray(img)
            normalized_image_array = (img.astype(np.float32) / 127.0) - 1
            normalized_image_array = np.expand_dims(normalized_image_array, axis=0)
            cv2.imshow('Bot_Ragnarok', img)

            now_state = get_class(normalized_image_array)
            print(labels[now_state])

            if labels[now_state] == 'done' and fishing_lock:
                time.sleep(0.2)
                game_screen.click('Done')
                fishing_lock = False
                time.sleep(4)
                continue
            if labels[now_state] == 'waiting' and not fishing_lock:
                game_screen.click('Start fishing')
                fishing_lock = True
                time.sleep(1)
                continue

        if cv2.waitKey(1) == ord('q'):
            break
        start_time = time.time()


# wait | proc -> proc -> wait -> done -> proc
# 0 | 1       -> 1    -> 0    -> 2    -> 1