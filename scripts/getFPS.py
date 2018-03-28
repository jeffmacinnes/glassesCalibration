"""
Report the FPS for each worldCamera.mp4 video found in the ./data directory
"""
# python 2/3 compatibility
from __future__ import division
from __future__ import print_function

import os
from os.path import join
import cv2
import numpy as np
import pandas as pd

# get the opencv version
OPENCV3 = (cv2.__version__.split('.')[0] == '3')
print("OPENCV version " + cv2.__version__)

# output
outputFile = open(join('../analysis', 'fps.txt'), 'w')

# walk through sub directories in the data dir
data_dir = '../data'
for f in os.listdir(data_dir):
    # only look in subject data directories
    if f[:3] in ['101', '102', '103']:

        # look for worldCamera.mp4
        try:
            vidFile = join(data_dir, f, 'worldCamera.mp4')
            vid = cv2.VideoCapture(vidFile)

            # retrieve the fps
            if OPENCV3:
                fps = vid.get(cv2.CAP_PROP_FPS)
            else:
                fps = vid.get(cv2.cv.CV_CAP_PROP_FPS)

            # write fps for this condition
            outputFile.write('{}\t{}\n'.format(f, fps))

            # close the video
            vid.release()
        except:
            print('No video file found for {}'.format(f))

# close output
outputFile.close()
