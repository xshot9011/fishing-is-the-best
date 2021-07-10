import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
import time
from get_image import ScreenCapture
import pandas as pd
import csv

fieldnames = ['x_value', 'y_value']
with open('data.csv', 'w') as f:
    csv_writer = csv.DictWriter(f, fieldnames=fieldnames)
    csv_writer.writeheader()

start_time = time.time()
loop_count = 1

while True:
    game_screen = ScreenCapture('NoxPlayer')
    game_screen.capture()
    # drawing circle
    if game_screen.image is not None:
        image = game_screen.get_crop_image()  
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,27,3)

        cnts = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        count = 0
        for c in cnts:
            area = cv2.contourArea(c)
            x,y,w,h = cv2.boundingRect(c)
            ratio = w/h
            ((x, y), r) = cv2.minEnclosingCircle(c)
            if ratio > .85 and ratio < 1.20 and area > 50 and area < 120 and r < 10:
                cv2.circle(image, (int(x), int(y)), int(r), (36, 255, 12), -1)
                count += 1
        
        # writing data
        with open('data.csv', 'a') as f:
            csv_writer = csv.DictWriter(f, fieldnames=fieldnames)
            info = {
                'x_value': loop_count,
                'y_value': count
            }
            loop_count += 1
            csv_writer.writerow(info)

        if count > 1:
            print('Count: {}'.format(count))

        cv2.imshow('thresh', thresh)
        cv2.imshow('image', image)
    # wait for exit key
    if cv2.waitKey(1) == ord('q'):
        break
    # print("FPS: {}".format(1/(time.time()-start_time)))
    start_time = time.time()
cv2.destroyAllWindows()