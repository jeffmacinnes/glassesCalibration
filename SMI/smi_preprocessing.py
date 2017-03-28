"""
Format raw SMI data. 

Tested with Python 3.6, open CV 3.2

The raw input data will be copied to a new directory stored in ./data. 
The output directory will be  named according to [mo-day-yr]/[hr-min-sec] of the original creation time format. 

The output directory will contain:
	- worldCamera.mp4: the video from the point-of-view scene camera on the glasses
	- frame_timestamps.tsv: table of timestamps for each frame in the world
	- gazeData_world.tsv: gaze data, where all gaze coordinates are represented w/r/t the world camera
"""

# python 2/3 compatibility
from __future__ import division
from __future__ import print_function

import sys, os, shutil
import argparse
from datetime import datetime
from os.path import join
import numpy as np
import pandas as pd


def preprocessData(inputDir, output_root):
	"""
	Run all preprocessing steps for SMI data
	"""
	### create output directory
	# figure out a way to get accurate timestamp to base directory on

	### Format the gaze data
	print('formatting gaze data...')
	# time is in microseconds
	# normalize gaze coordinates relative to video frame
	# convert frame column to intelligible frame_idx
	# create confidence column based on Event labels


	### Copy and rename the movie file







if __name__ == '__main__':
	# parse arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('inputDir', help='path to the raw pupil labs recording dir')
	parser.add_argument('outputDir', help='output directory root. Raw data will be written to recording specific dirs within this directory')
	args = parser.parse_args()

	# check if input directory is valid
	if not os.path.isdir(args.inputDir):
		print('Invalid input dir: {}'.format(args.inputDir))
		sys.exit()
	else:

		# run preprocessing on this data
		preprocessData(args.inputDir, args.outputDir)