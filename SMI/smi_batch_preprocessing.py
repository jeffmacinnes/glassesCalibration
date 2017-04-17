import os
from os.path import join
import pandas as pd 

# conditions
sessions = [3,4,5,6,7,8,9,10,11]

raw_dir = './data/5-53'
output_dir = './data/'

for s in sessions:
	cmd_str = ' '.join(['python', 'smi_preprocessing.py', raw_dir, str(s), output_dir])
	print(cmd_str)
	try:
		os.system(cmd_str)
	except:
		print('failed on: {}'.format(cmd_str))

