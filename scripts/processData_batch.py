"""
Batch submit multiple subjects to the proccessData script
"""

import os
from os.path import join
import pandas as pd 

conditions = ['101_Tobii_2M_0deg',
			'101_Tobii_2M_10Ldeg',
			'101_Tobii_2M_10Rdeg',
			'101_Tobii_3M_0deg',
			'101_Tobii_3M_10Ldeg',
			'101_Tobii_3M_10Rdeg']

conditions = ['101_Tobii_3M_0deg']

# load the metadata table
metadata_df = pd.read_table(join('../data', 'metadataTable.txt'), sep='\t', header=0)

# create new column that concatenates subfields to match condition formatting
metadata_df['condition'] = metadata_df['Subj'].map(str) + '_' + metadata_df['Glasses'] + '_' + metadata_df['Distance'] + '_' + metadata_df['Offset']


for cond in conditions:
	print('Submitting job for: {}'.format(cond))

	thisRow = metadata_df.loc[metadata_df.condition == cond]
	
	# set up inputs
	preprocDir = join('..', thisRow.Glasses.iloc[0], 'data', thisRow.Date.iloc[0])



	try:
		cmd_str = 'python processData.py ' + preprocDir + ' ' + cond 
		os.system(cmd_str)
	except:
		print('FAILED TO RUN:  {}'.format(cond))
