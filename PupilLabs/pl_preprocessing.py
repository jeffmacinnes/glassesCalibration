"""
Format raw Pupil Labs data. 

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
import csv
from itertools import chain

try:
	import cPickle as pickle
except ImportError:
	import pickle


def preprocessData(inputDir, output_root):
	""" 
	Run all preprocessing steps for pupil lab data
	"""

	### Copy the raw data to a new directory
	print('copying files...')
	outputDir = copyPupilLabRecording(inputDir, output_root)

	### Format the gaze data
	print('formatting gaze data...')
	gazeData_world, frame_timestamps = formatGazeData(inputDir)

	### write the gazeData to to a csv file
	print('writing file to csv...')
	csv_file = join(outputDir, 'gazeData_world.tsv')
	export_range = slice(0, len(gazeData_world))
	with open(csv_file, 'w', encoding='utf-8', newline='') as csvfile:
		csv_writer = csv.writer(csvfile, delimiter='\t')
		csv_writer.writerow(("timestamp",
							"frame_idx",
							"confidence",
							"norm_pos_x",
							"norm_pos_y"))
		for g in list(chain(*gazeData_world[export_range])):
			data = ['{}'.format(g["timestamp"]), 
								g["frame_idx"], 
								g["confidence"],  
								g["norm_pos"][0], 
								g["norm_pos"][1]]  # use str on timestamp to be consitant with csv lib.
			csv_writer.writerow(data)




def copyPupilLabRecording(inputDir, output_root):
	""" 
	create a new output directory and copy the relevant files to it
	"""
	# get the timestamp from the info.csv file
	info_file = join(inputDir, 'info.csv')
	with open(info_file, 'r') as f:
		for line in f:
			if 'Start Date' in line:
				startDate = datetime.strptime(line.split(',')[1].strip('\n'), '%d.%m.%Y')
				date_dir = startDate.strftime('%Y_%m_%d')
			if 'Start Time' in line:
				startTime = datetime.strptime(line.split(',')[1].strip('\n'), '%H:%M:%S')
				time_dir = startTime.strftime('%H-%M-%S')

	# create the output directory (if necessary)
	outputDir = join(output_root, date_dir, time_dir)
	if not os.path.isdir(outputDir):
		os.makedirs(outputDir)

	# check if directory is empty, copy files over if so
	for dirpath, dirnames, files in os.walk(outputDir):
		if not files:
			for f in ['world_timestamps.npy', 'pupil_data']:
				shutil.copyfile(join(inputDir, f), join(outputDir, f))

	# return the path to the new output directory
	return outputDir


def formatGazeData(inputDir):
	"""
	- load the pupil_data and timestamps
	- get the "gaze" fields from pupil data (i.e. the gaze lcoation w/r/t world camera)
	- sync gaze data with the world_timestamps array
	"""

	# load pupil data
	pupil_data_path = join(inputDir, 'pupil_data')
	try:
		with open(pupil_data_path, 'rb') as fh:
			pupil_data = pickle.load(fh, encoding='bytes')
	except pickle.UnpicklingError:
		raise ValueError
	gaze_list = pupil_data['gaze_positions']   # gaze posiiton (world camera)

	# load timestamps
	timestamps_path = join(inputDir, 'world_timestamps.npy')
	frame_timestamps = np.load(timestamps_path)

	# align gaze with world camera timestamps
	gaze_by_frame = correlate_data(gaze_list, frame_timestamps)

	return gaze_by_frame, frame_timestamps


def correlate_data(data,timestamps):
	'''
	data:  list of data :
		each datum is a dict with at least:
			timestamp: float

	timestamps: timestamps list to correlate  data to

	this takes a data list and a timestamps list and makes a new list
	with the length of the number of timestamps.
	Each slot contains a list that will have 0, 1 or more assosiated data points.

	Finally we add an index field to the datum with the associated index
	'''
	timestamps = list(timestamps)
	data_by_frame = [[] for i in timestamps]

	frame_idx = 0
	data_index = 0

	data.sort(key=lambda d: d['timestamp'])

	while True:
		try:
			datum = data[data_index]
			# we can take the midpoint between two frames in time: More appropriate for SW timestamps
			ts = ( timestamps[frame_idx]+timestamps[frame_idx+1] ) / 2.
			# or the time of the next frame: More appropriate for Sart Of Exposure Timestamps (HW timestamps).
			# ts = timestamps[frame_idx+1]
		except IndexError:
			# we might loose a data point at the end but we dont care
			break

		if datum['timestamp'] <= ts:
			datum['frame_idx'] = frame_idx
			data_by_frame[frame_idx].append(datum)
			data_index +=1
		else:
			frame_idx+=1

	return data_by_frame



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



