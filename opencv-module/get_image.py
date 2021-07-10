#!/bin/env python3
# Screen Capture module writed by win32api
import time
import cv2
import numpy as np
import win32gui
import win32ui
import win32con
import win32api

class ScreenCapture:
    def __init__(self, window_name, image=None, position=[]):
        self.window_name = window_name
        self.image = image
        # position [left,top,right,bottom]
        self.position = position
        self.window = win32gui.FindWindow(None, window_name)

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
    
    def send_click(self, X_START_PROPORTION=0.75, Y_START_PROPORTION=0.625, X_FLAG_PROPORTION=0.075, Y_FLAG_PROPORTION=0.125):
        width, height = self.image.shape[1], self.image.shape[0]
        x_start = int(X_START_PROPORTION*width)
        y_start = int(Y_START_PROPORTION*height)
        x_step = int(X_FLAG_PROPORTION*width)
        y_step = int(Y_FLAG_PROPORTION*height)
        lParam = win32api.MAKELONG(x_start+x_step, y_start+y_step)
        win32gui.SendMessage(self.window, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        win32gui.SendMessage(self.window, win32con.WM_LBUTTONUP, None, lParam)

if __name__ == "__main__":
    # os.chdir(os.path.dirname(os.path.abspath(__file__)))

    start_time = time.time()
    while True:
        game_screen = ScreenCapture('NoxPlayer')
        game_screen.capture()

        # Display
        if game_screen.image is not None:
            cv2.imshow('Bot_Ragnarok', game_screen.resize(50))

        if cv2.waitKey(1) == ord('q'):
            break
        print("FPS: {}".format(1/(time.time()-start_time)))
        start_time = time.time()

    cv2.destroyAllWindows()
