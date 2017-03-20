"""
step 3: Analyze the Calibration performance for a given run

Assumes processData.py has already been run. 

all of the output will be stored in a 'calibration' direction in ./data/<condition name>
Output directory will contain the following files:
	- calibration_gazeData.tsv: all of the gaze data aligned with the calibration task trials
	- calibration_summarized.tsv: a summary of calibration accuracy and precision on each calibration point
	- calibrationPlot_raw.pdf: plot of all of the gaze data, colored by trial
	- calibrationPlot_summary.pdf: plot of summarized accuracy and precision on this run
	- <condition name>_taskLog.txt: the trial timinig for this run
	- firstFrame_<####>.jpg: image of the frame on which the start image was found
	- firstFrame.txt: text file containing the frame number of the start image
"""

# python 2/3 compatibility
from __future__ import division
from __future__ import print_function

import os, sys
import shutil
import cv2
import argparse
import numpy as np
import pandas as pd
from os.path import join

### Configuration vars
startImage_path = '../task/startImage.jpg'
trialDur = 3000
trialWin = (500, 2500)

# dict to store the pixels/deg visual angle on the calibration grid at various distances
pixPerDeg = {'1M': 85.8, '2M': 171.2, '3M': 256.7}

# dict to store the fps of gaze data based on different glasses models
gaze_fps = {'Tobii': 50, 'PL': 30, 'SMI':0000}

def processCalibration(condition):
	"""
	process the calibration data for this condition. 
	"""

	# parse condition
	subj, glasses, distance, offset = condition.split('_')

	# store the maximum number of gazepts per trial under ideal conditons for these glasses
	idealMaxGazePts = int((trialWin[1]-trialWin[0])/1000 * gaze_fps[glasses])
	print(idealMaxGazePts)

	### set up inputs/outputs
	dataDir = join('../data', condition)
	procDir = join(dataDir, 'processed')
	calibDir = join(dataDir, 'calibration')

	# create calibration output dir
	if not os.path.isdir(calibDir):
		os.makedirs(calibDir)

	# copy the task log for this condition to the calibration dir
	taskLog_fname = join('../data', 'taskLogs', (condition + '_taskLog.txt'))
	if os.path.exists(taskLog_fname):
		shutil.copy(taskLog_fname, calibDir)
	else:
		print('Could not find task log for: {}'.format(condition))

	### find the video frame where the start image appears
	if not os.path.exists(join(calibDir, 'startFrame.txt')):
		print('Searching for task start frame...')
		startFrameNum, startFrame = findStartFrame(join(dataDir, 'worldCamera.mp4'))
		cv2.imwrite(join(calibDir, ('startFrame_' + str(startFrameNum).zfill(4) + '.jpg')), startFrame)
		with open(join(calibDir, 'startFrame.txt'), 'w') as f:
			f.write(str(startFrameNum))
	else:
		# if already done, just read the text file
		with open(join(calibDir, 'startFrame.txt'), 'r') as f:
			startFrameNum = int(f.read())

	### find the timestamp of the start image
	gazeWorld_df = pd.read_table(join(dataDir, 'gazeData_world.tsv'), sep='\t')
	startImage_df = gazeWorld_df[gazeWorld_df.frame_idx == (startFrameNum-1)].iloc[0]
	taskStartTime = startImage_df.timestamp
	print(taskStartTime)

	### Load the mapped gaze data, add column with ts relative to the task
	gaze_df = pd.read_table(join(procDir, 'gazeData_mapped.tsv'), sep='\t')
	gaze_df.loc[:, 'task_ts'] = gaze_df.gaze_ts - taskStartTime

	### Load the task log start times
	taskLog = pd.read_table(join(calibDir, (condition + '_taskLog.txt')))
	calibGridDims = (taskLog.col.max(), taskLog.row.max())

	### Loop through each calibration point
	for i in range(taskLog.shape[0]):
		# each point is pd.series object with entries for Col, Row, and Time
		thisPt = taskLog.iloc[i]

		# get trial start time for this pt
		trialStart = thisPt.time

		# figure out the index location of this point (counting from L->R, T->B)
		ptIdx = (thisPt.row-1) * calibGridDims[0] + thisPt.col

		# isolate the gaze data that corresponds to this pt only
		trialGaze_df = gaze_df[(gaze_df.task_ts > trialStart) & (gaze_df.task_ts <= (trialStart + trialDur))]

		# Insert col of timestamps relative to the trial onset
		trialGaze_df.loc[:, 'trial_ts'] = trialGaze_df.task_ts - trialStart

		# isolate the trial data to only those timepoints that fall within the specified analysis window
		trialGaze_df = trialGaze_df[(trialGaze_df.trial_ts > trialWin[0]) & (trialGaze_df.trial_ts <= trialWin[1])]

		# analyze the trial, if there's any data for this trial
		if trialGaze_df.shape[0] > 0:
			# add info about the calibraiton point to the dataframe
			trialGaze_df['col'] = thisPt.col
			trialGaze_df['row'] = thisPt.row
			trialGaze_df['ptIdx'] = ptIdx

			# calculate gaze point distance/angle from the ideal location
			idealLocation = ((1000/6)*thisPt.col, (1000/6)*thisPt.row)
			trialGaze_df.loc[:, 'distance'] = trialGaze_df.apply(lambda d: getDistance(idealLocation[0],
																						idealLocation[1], 
																						d['calibGrid_gazeX'], 
																						d['calibGrid_gazeY'],
																						distance), axis=1)
			trialGaze_df.loc[:, 'angle'] = trialGaze_df.apply(lambda d: getAngle(idealLocation[0], 
																					idealLocation[1], 
																					d['calibGrid_gazeX'],
																					d['calibGrid_gazeY']), axis=1)

			# drop datapts where the distance is more than 5 deg of visual angle away from calib pt
			trialGaze_df = trialGaze_df[trialGaze_df['distance'] < 5]

			### Summarize this trial ################################
			# calculate percent of valid timepts
			percentValid = trialGaze_df.shape[0]/idealMaxGazePts

			# calculate centroid coords (mean gaze X,Y in calib coordinate space)
			centroidX = np.mean(trialGaze_df.calibGrid_gazeX)
			centroidY = np.mean(trialGaze_df.calibGrid_gazeY)

			# calculate distance and angle from ideal for the centroid
			centDist = getDistance(idealLocation[0], idealLocation[1], centroidX, centroidY, distance)
			centAngle = getAngle(idealLocation[0], idealLocation[1], centroidX, centroidY)

			# calculate precision: RMS (root mean squared) of distance between each gazept and centroid
			distFromCentroid = trialGaze_df.apply(lambda d: getDistance(centroidX,
																		centroidY,
																		d['calibGrid_gazeX'], 
																		d['calibGrid_gazeY'],
																		distance), axis=1)
			RMS = np.sqrt(np.sum(np.square(distFromCentroid)) * (1/distFromCentroid.shape[0]))

			# write all of this trial's data to a dataframe
			trialSummary = pd.DataFrame({'ptIdx':ptIdx,
											'percentValid':percentValid,
											'centX':centroidX, 'centY':centroidY,
											'RMS':RMS,
											'centDist':centDist, 'centAngle':centAngle}, index=[0])

			# add this trial summary to the master dataframe for all trials
			if i == 0:
				gazeCalibration_df = trialGaze_df.copy()
				allTrials_summarized = trialSummary.copy()
			else:
				gazeCalibration_df = pd.concat([gazeCalibration_df, trialGaze_df], join='outer', ignore_index=True)
				allTrials_summarized = pd.concat([allTrials_summarized, trialSummary], join='outer', ignore_index=True)

	# Write to text files
	gazeCalibration_df.to_csv(join(calibDir, 'gazeData_calibration.tsv'), sep='\t', index=False, float_format='%.3f')
	allTrials_summarized.to_csv(join(calibDir, 'calibrationSummary.tsv'), sep='\t', index=False, float_format='%.3f')



def getDistance(x1,y1,x2,y2, distance):
	# calculate vector distance between two points, return distance in terms of visual angle
	xDist = x2-x1
	yDist = y2-y1
	gazeDistance = (np.sqrt(xDist**2 + (yDist**2)))/pixPerDeg[distance]
	return gazeDistance


def getAngle(x1,y1,x2,y2):
	# calculate vector angle between two points
	xDist = x2-x1
	yDist = (y2-y1)
	return 360-np.rad2deg(np.arctan2(yDist,xDist))


def findMatches(img1_kp, img1_des, img2_kp, img2_des):
	"""
	Find the matches between the descriptors for two images
		Inputs: 	keypoints, descriptors each image
		Output: 	2D coords of quaifying matches on img1, 2D coords of qualifying matches on img2
	"""
	# Match settings
	min_match_count = 50
	min_good_matches = 4
	num_matches = 2
	FLANN_INDEX_KDTREE = 0
	distance_ratio = 0.5				# 0-1; lower values more conservative
	index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
	search_params = dict(checks=10)		# lower = faster, less accurate
	matcher = cv2.FlannBasedMatcher(index_params, search_params)

	# find all matches
	matches = matcher.knnMatch(img1_des, img2_des, k=num_matches)

	# filter out cases where the 2 matches (best guesses) are too close to each other
	goodMatches = []
	for m,n in matches:
		if m.distance < distance_ratio*n.distance:
			goodMatches.append(m)

	if len(goodMatches) > min_good_matches:
		img1_pts = np.float32([img1_kp[i.queryIdx].pt for i in goodMatches])
		img2_pts = np.float32([img2_kp[i.trainIdx].pt for i in goodMatches])

		return img1_pts, img2_pts
	
	else:
		return None, None


def findStartFrame(vidPath):
	"""
	find the first frame in the video in which the startImage appears
	"""
	OPENCV3 = (cv2.__version__.split('.')[0] == '3')
	
	# open vid file, set parameters
	vid = cv2.VideoCapture(vidPath)
	if OPENCV3:
		totalFrames = vid.get(cv2.CAP_PROP_FRAME_COUNT)
		featureDetect = cv2.xfeatures2d.SIFT_create()
	else:
		totalFrames = vid.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
		featureDetect = cv2.SIFT()

	# find features, kp & des, for start image
	startImg = cv2.imread(startImage_path)
	startImg = cv2.cvtColor(startImg, cv2.COLOR_BGR2GRAY)
	startImg_kp, startImg_des = featureDetect.detectAndCompute(startImg, None)
	print('Task Start Image: found {} keypoints'.format(len(startImg_kp)))

	# loop through video frames until the startImage is found
	frameCounter = 1
	print('searching frame: ')
	while vid.isOpened():
		# read the next frame of the video
		ret, frame = vid.read()

		# check if its valid
		if ret == True:
			print(frameCounter, end=', ', flush=True)

			origFrame = frame.copy()	# create a copy of the original frame
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

			# ID keypoints on this frame
			frame_kp, frame_des = featureDetect.detectAndCompute(frame, None)

			# Look for matches with start Image
			startPts, framePts = findMatches(startImg_kp, startImg_des, frame_kp, frame_des)
			if (startPts is not None):
				if len(startPts) > 25:
					print("found {} start cue matches on frame {}".format(len(startPts), frameCounter))
					startFrame = origFrame
					startFrameNum = frameCounter

					# close the video
					vid.release()

			# increment frameCounter
			frameCounter += 1
			if frameCounter == totalFrames:
				print('Never found the start image!')
				vid.release()

	return startFrameNum, startFrame










if __name__ == '__main__':
	# parse arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('condition', help='name of the experimental condition (e.g. 101_Tobii_1M_0deg')
	args = parser.parse_args()

	# check if valid condition
	if not os.path.isdir(join('../data', args.condition, 'processed')):
		print('Cannot find a "Processed" directory in ./data/{}'.format(args.condition))
	else:
		processCalibration(args.condition)
