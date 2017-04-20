import os
from os.path import join
import pandas as pd


# load the file mapping table
#df = pd.read_table('./data/Tobii_fileName_mapping.txt', sep='\t', header=0)


TobiiNames = ['mxtjzks',
				'y5fzpzu',
				'krqosis',
				'sooa4nn',
				'rhw4enq',
				'tlrce7e',
				'ynl5mtd',
				'i4vkpjx',
				'rgvyhc3']

output_dir = './data/'
for d in TobiiNames:
	raw_dir = join('./data/raw', d, 'segments/1')
	cmd_str = ' '.join(['python', 'tobii_preprocessing.py', raw_dir, output_dir])
	print(raw_dir)
	try:
		os.system(cmd_str)
	except:
		print('failed on: {}'.format(cmd_str))
