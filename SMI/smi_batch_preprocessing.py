import os
from os.path import join
import pandas as pd

# conditions
sessions = [2,3,4]

raw_dir = './data/raw/3-36'
output_dir = './data'

for s in sessions:
	cmd_str = ' '.join(['python', 'smi_preprocessing.py', raw_dir, str(s), output_dir])
	print(cmd_str)
	try:
		os.system(cmd_str)
	except:
		print('failed on: {}'.format(cmd_str))
