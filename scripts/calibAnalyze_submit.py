import os
import sys


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
			'j_0deg_A',
			'j_0deg_B',
			'j_0deg_C',
			'j_0deg_down',
			'j_5deg_L',
			'j_5deg_R',
			'j_10deg_L',
			'j_10deg_R',
			'j_15deg_L',
			'j_15deg_R']

for c in conds:
	print c
	os.system(('python calibrationAnalyze.py ' + c))