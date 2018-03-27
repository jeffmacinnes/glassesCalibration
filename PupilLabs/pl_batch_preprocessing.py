import os
from os.path import join
import pandas as pd


# conditions
sessions = [0,2,3,4,5,6,8,12,13,15,18,20,21,23,24,26]
raw_dir = './data/raw/2017_05_26'
output_dir = './data'

for s in sessions:
    cmd_str = ' '.join(['python', 'pl_preprocessing.py', join(raw_dir, str(s).zfill(3)), output_dir])
    print(cmd_str)

    try:
        os.system(cmd_str)
    except:
        print('failed on: {}'.format(cmd_str))
