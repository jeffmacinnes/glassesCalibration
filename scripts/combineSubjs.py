import os
import sys
from os.path import join, dirname
import numpy as np
import pandas as pd

conds = ['e_0deg',
			'e_5deg_L',
			'e_5deg_R',
			'e_10deg_L',
			'e_10deg_R',
			'e_15deg_L',
			'e_15deg_R',
			'k_0deg',
			'k_5deg_L',
			'k_5deg_R',
			'k_10deg_L',
			'k_10deg_R',
			'k_15deg_L',
			'k_15deg_R',
			'j_0deg',
			'j_5deg_L',
			'j_5deg_R',
			'j_10deg_L',
			'j_10deg_R',
			'j_15deg_L',
			'j_15deg_R']

# set up paths
scriptDir = dirname(os.path.realpath(__file__))
EXP_DIR = dirname(scriptDir)

analysisDir = join(EXP_DIR, 'analysis')
dataDir = join(EXP_DIR, 'data')

for i,cond in enumerate(conds):
	print cond

	# parse the condition name
	condParts = cond.split('_')
	subj = condParts[0]
	offset = '_'.join(condParts[1:])

	# path to this subject/cond data
	condData_fname = join(dataDir, cond, 'output/calibrationSummarized.csv')

	# import as pandas dataframe
	cond_df = pd.read_csv(condData_fname, sep='\t')

	# add conditon as column to dataframe
	cond_df['condition'] = cond
	cond_df['subj'] = subj
	cond_df['offset'] = offset

	# concatenate into a full dataset
	if i == 0:
		allSubjs = cond_df.copy()
	else:
		allSubjs = pd.concat([allSubjs, cond_df], join='outer', ignore_index=True)
	

# write output
print allSubjs.head()
allSubjs.to_csv(join(analysisDir, 'allConds_uniqueSubjs.csv'), index=False, sep='\t', float_format='%.2f')
