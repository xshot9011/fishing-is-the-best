import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
import time
import win32gui
import win32api
import win32con
from numpy.core.fromnumeric import mean
from get_image import ScreenCapture
import pandas as pd
import csv

is_tuning_phase = True
is_bating_click = False
is_enable_set_trigger_max = False

while True:
    hwnd = win32gui.FindWindow(None, 'NoxPlayer')
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top

    data = pd.read_csv('data.csv')
    x = data['x_value'][-300:]
    y = data['y_value'][-300:]
    if is_tuning_phase and not is_bating_click:
        print('tuning')
        normal_min = min(y)
        normal_max = max(y)
        normal_avg = mean(y)
        trigger_max = normal_max
        slope = '-' if y.iloc[-1] < normal_max else '+'
        print(f'min: {normal_min}, max: {normal_max}, avg: {round(normal_avg)}, trigger_max: {trigger_max}')
        is_tuning_phase = False
        is_enable_set_trigger_max = True
        x_start = int(0.75*width)
        y_start = int(0.625*height)
        x_step = int(0.075*width)
        y_step = int(0.125*height)
        lParam = win32api.MAKELONG(x_start+x_step, y_start+y_step)
        win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, None, lParam)
        continue

    if is_enable_set_trigger_max:
        print('set max')
        if max(y) > normal_max + 5:
            trigger_max = max(y)
            is_enable_set_trigger_max = False
            is_bating_click = True
            continue

    if is_bating_click and not is_enable_set_trigger_max:
        print('baiting')
        if y.iloc[-1] <= trigger_max - 4:
            print(y.iloc[-1], trigger_max)
            print('Click')
            x_start = int(0.75*width)
            y_start = int(0.625*height)
            x_step = int(0.075*width)
            y_step = int(0.125*height)
            lParam = win32api.MAKELONG(x_start+x_step, y_start+y_step)
            win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, None, lParam)
            time.sleep(4)
            is_bating_click = False
            is_tuning_phase = True
            continue