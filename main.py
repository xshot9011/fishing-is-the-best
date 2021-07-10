import cv2
import csv
import numpy as np
from numpy.core.fromnumeric import mean
from numpy.lib.utils import info
import pandas as pd
import win32gui
import win32ui
import win32con
import win32api
import time
import matplotlib.pyplot as plt

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

    def _set_position(self, hwnd):
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        self.position.append(left)
        self.position.append(top)
        self.position.append(right)
        self.position.append(bottom)

    def capture(self):
        # locate window
        hwnd = win32gui.FindWindow(None, self.window_name)
        if hwnd:
            # set window position
            self._set_position(hwnd)
            width = self.position[2] - self.position[0]
            height = self.position[3] - self.position[1]

            # try to crop border
            border_pixel = 0
            titlebar_pixel = 0
            width = width - (border_pixel * 2)
            height = height - (titlebar_pixel + (border_pixel))

            # Create BitMap for Screenshot
            wDC = win32gui.GetWindowDC(hwnd)
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
            win32gui.ReleaseDC(hwnd, wDC)
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

    def get_circles_number(self):
        gray = cv2.cvtColor(self.get_crop_image(), cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 27, 3)

        cnts = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        
        count = 0
        for c in cnts:
            area = cv2.contourArea(c)
            x, y, w, h = cv2.boundingRect(c)
            ratio = w/h
            ((x, y), r) = cv2.minEnclosingCircle(c)
            if ratio > .85 and ratio < 1.20 and area > 50 and area < 120 and r < 10:
                count += 1
        return count

    def write_to_csv(self, x, y, file_name='data.csv', fieldnames=['x_value', 'y_value']):
        with open(file_name, 'a') as f:
            csv_writer = csv.DictWriter(f, fieldnames=fieldnames)
            info = {
                'x_value': x,
                'y_value': y
            }
            csv_writer.writerow(info)

class Bot:
    __slots__ = [
        'window_name', 'hwnd', 'metadata',
        'X_START_PROPORTION', 'Y_START_PROPORTION', 'X_FLAG_PROPORTION', 'Y_FLAG_PROPORTION'
    ]

    def __init__(self, window_name: str) -> None:
        self.window_name = window_name
        self.generate_metadata()

        # constant initial
        self.X_START_PROPORTION = 0.75
        self.Y_START_PROPORTION = 0.625
        self.X_FLAG_PROPORTION = 0.15
        self.Y_FLAG_PROPORTION = 0.25
        
    def generate_metadata(self):
        self.hwnd = win32gui.FindWindow(None, self.window_name)
        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        self.metadata = {
            'width' : right-left,
            'height': bottom-top,
            'top'   : top,
            'bottom': bottom,
            'right' : right,
            'left'  : left
        }
    
    def get_process_data(self, filename='data.csv', fieldnames=['x_value', 'y_value']):
        data = pd.read_csv('data.csv')
        if len(data) > 300:
            x = data['x_value'][-300:]
            y = data['y_value'][-300:]

            return {
                'min': min(y),
                'max': max(y),
                'avg': round(mean(y)),
                'last': y.iloc[-1]
            }
        return {
            'min': min(data['y_value']),
            'max': max(data['y_value']),
            'avg': round(mean(data['y_value']), 1),
            'last': 0
        }

    def click(self, msg=None):
        if msg is not None:
            print(msg)
        x_start = int(self.X_START_PROPORTION*self.metadata['width'])
        y_start = int(self.Y_START_PROPORTION*self.metadata['height'])
        x_step = int((self.X_FLAG_PROPORTION/2)*self.metadata['width'])
        y_step = int((self.Y_FLAG_PROPORTION/2)*self.metadata['height'])
        l_parameter = win32api.MAKELONG(x_start+x_step, y_start+y_step)
        
        win32gui.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_parameter)
        win32gui.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, None, l_parameter)

if __name__ == "__main__":
    WINDOW_NAME = 'NoxPlayer'
    IS_DEBUG = True
    TUNING_STACK_REQUIRE = 100
    TUNING_LIMIT_TIME = 4
    SETTING_TRIGGER_LIMIT_TIME = 10
    TRIGGER_DECREASE_SAMPLE_REQUIRE = 2
    
    fieldnames = ['x_value', 'y_value']
    with open('data.csv', 'w') as f:
        csv_writer = csv.DictWriter(f, fieldnames=fieldnames)
        csv_writer.writeheader()

    is_tuning_phase = True
    is_enable_set_trigger_max = False
    is_bating_click = False

    normal_min = None
    normal_max = None
    normal_avg = None
    normal_avg_stack = 0
    decrease_sample_stack = 0
    trigger_max = None

    phase_timer = None

    loop_count = 1
    while True:
        game_screen = ScreenCapture(WINDOW_NAME)
        game_screen.capture()
        bot = Bot(WINDOW_NAME)
        bot.generate_metadata()

        # Process
        if game_screen.image is not None:
            count = game_screen.get_circles_number()
            game_screen.write_to_csv(loop_count, count)
        
        # Tuning normal value
        information = bot.get_process_data()
        if is_tuning_phase:
            if phase_timer is None:
                phase_timer = time.time()
            if time.time()-phase_timer > TUNING_LIMIT_TIME:
                print('Reset timer of tuning phase ============================================================')
                phase_timer = None
                normal_avg = None
                normal_avg_stack = 0
            if normal_avg_stack > TUNING_STACK_REQUIRE:
                bot.click('Start fishing')
                normal_min = information['min']
                normal_max = information['max']
                normal_avg = information['avg']
                phase_timer = None
                normal_avg_stack = 0
                is_tuning_phase = False
                is_enable_set_trigger_max = True
            if normal_avg is None:
                normal_min = information['min']
                normal_max = information['max']
                normal_avg = information['avg']
            if abs(normal_avg-information['avg']) < 0.2 and abs(normal_max-information['max']) <= 1:
                normal_avg_stack += 1
        
        if is_enable_set_trigger_max:
            if phase_timer is None:
                phase_timer = time.time()
            if information['max'] >= normal_max + 5:
                print(f'max trigger: {information["max"]}')
                trigger_max = information['max']
                phase_timer = None
                is_enable_set_trigger_max = False
                is_bating_click = True
        
        if is_bating_click:
            if information['last'] < trigger_max - 4:
                print(trigger_max, information['last'])
                bot.click('Click from bot')
                # click action
                time.sleep(3)
                is_bating_click = False
                is_tuning_phase = True  
        # ending loop
        loop_count += 1
