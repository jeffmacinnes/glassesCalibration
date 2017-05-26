"""
Batch submit multiple subjects to the analyzeCalibration script
"""

import os
from os.path import join
import pandas as pd

conditions = []
for subj in ['102']:
	for glasses in ['PupilLabs']:
		for dist in ['1M']:
			for offset in ['0deg', '10Ldeg', '10Rdeg']:
				thisCond = '_'.join([subj, glasses, dist, offset])
				conditions.append(thisCond)

# # load the metadata table
# metadata_df = pd.read_table(join('../data', 'metadataTable.txt'), sep='\t', header=0)
#
# # create new column that concatenates subfields to match condition formatting
# metadata_df['condition'] = metadata_df['Subj'].map(str) + '_' + metadata_df['Glasses'] + '_' + metadata_df['Distance'] + '_' + metadata_df['Offset']


for cond in conditions:
	print('Submitting job for: {}'.format(cond))

	try:
		cmd_str = 'python analyzeCalibration.py ' + cond
		os.system(cmd_str)
	except:
		print('FAILED TO RUN:  {}'.format(cond))
