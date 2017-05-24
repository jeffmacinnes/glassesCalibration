import os
from os.path import join
import pandas as pd


# conditions
sessions = [0,1,2]
raw_dir = './data/raw/2017_05_24'
output_dir = './data'

for s in sessions:
    cmd_str = ' '.join(['python', 'pl_preprocessing.py', join(raw_dir, str(s).zfill(3)), output_dir])
    print(cmd_str)

    try:
        os.system(cmd_str)
    except:
        print('failed on: {}'.format(cmd_str))
