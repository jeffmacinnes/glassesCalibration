import os
from os.path import join
import pandas as pd


# conditions
sessions = [0,2,3,4,5,6,7,10,11,12,13,14,15]
raw_dir = './data/raw/2017_05_25'
output_dir = './data'

for s in sessions:
    cmd_str = ' '.join(['python', 'pl_preprocessing.py', join(raw_dir, str(s).zfill(3)), output_dir])
    print(cmd_str)

    try:
        os.system(cmd_str)
    except:
        print('failed on: {}'.format(cmd_str))
