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
import pandas as import pd

# get the opencv version
OPENCV3 = (cv2.__version__.split('.')[0] == '3')
print("OPENCV version " + cv2.__version__)

# walk through sub directories in the data dir
data_dir = '../data'
for f in os.listdir(data_dir):
    # only look in subject data directories
    if f[:3] in ['101', '102', '103']:
        print f
