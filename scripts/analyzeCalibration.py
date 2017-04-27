"""
step 3: Analyze the Calibration performance for a given run

Assumes processData.py has already been run.

all of the output will be stored in a 'calibration' directory (e.g. ./data/<condition name>/calibration).
This directory will contain the following files:
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
import matplotlib
matplotlib.use('tkagg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

### Configuration vars
startImage_path = '../task/startImage.jpg'
trialDur = 3000
trialWin = (500, 2500)
calibGrid_path = '../referenceGrids/calibrationGrid.jpg'

# dict to store the pixels/deg visual angle on the calibration grid at various distances
# The calibration grid is 1000px on edge, and 204mm on edge in the real world
pixPerDeg = {'1M': 85.8, '2M': 171.2, '3M': 256.7}

# dict to store the fps of gaze data based on different glasses models
gaze_fps = {'Tobii': 50, 'PL': 60, 'SMI': 60}

def processCalibration(condition):
	"""
	process the calibration data for this condition.
	"""

	# parse condition
	subj, glasses, distance, offset = condition.split('_')

	# store the maximum number of gazepts per trial based on the trial window and glasses sampling Hz
	idealMaxGazePts = int((trialWin[1]-trialWin[0])/1000 * gaze_fps[glasses])

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

		thisTrial = str(i+1)

		# get trial start time for this pt
		trialStart = thisPt.time

		# figure out the index location of this point (counting from L->R, T->B)
		ptIdx = (thisPt.row-1) * calibGridDims[0] + thisPt.col

		# isolate the gaze data that corresponds to this pt only (return a copy of the gaze_df dataframe)
		trialGaze_df = gaze_df[(gaze_df.task_ts > trialStart) & (gaze_df.task_ts <= (trialStart + trialDur))].copy()

		# Insert col of timestamps relative to the trial onset
		# trialGaze_df.assign(trial_ts = lambda x: x.task_ts - trialStart)
		# print(trialGaze_df.columns)
		trialGaze_df['trial_ts'] = trialGaze_df.task_ts - trialStart

		# isolate the trial data to only those timepoints that fall within the specified analysis window
		trialGaze_df = trialGaze_df[(trialGaze_df.trial_ts > trialWin[0]) & (trialGaze_df.trial_ts <= trialWin[1])]

		# analyze the trial, if there's any data for this trial
		if trialGaze_df.shape[0] > 0:
			# add info about the calibraiton point to the dataframe
			trialGaze_df['col'] = thisPt.col
			trialGaze_df['row'] = thisPt.row
			trialGaze_df['ptIdx'] = ptIdx
			trialGaze_df['trial'] = thisTrial

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


			# Add this trial's data to the master dataframe for all trials
			if 'gazeCalibration_df' not in locals():
				gazeCalibration_df = trialGaze_df.copy()
			else:
				gazeCalibration_df = pd.concat([gazeCalibration_df, trialGaze_df], join='outer', ignore_index=True)

			# drop datapts where the distance is more than 5 deg of visual angle away from calib pt
			trialGaze_df = trialGaze_df[trialGaze_df['distance'] < 5]

			if trialGaze_df.shape[0] > 0:
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
				trialSummary = pd.DataFrame({'trial': thisTrial,
												'ptIdx':ptIdx,
												'percentValid':percentValid,
												'centX':centroidX, 'centY':centroidY,
												'RMS':RMS,
												'centDist':centDist, 'centAngle':centAngle}, index=[0])
			else:
				# if no datapts are less than 5 deg away from where they should be, write Nans
				trialSummary = pd.DataFrame({'trial': thisTrial,
												'ptIdx':ptIdx,
												'percentValid':0,
												'centX':np.nan, 'centY':np.nan,
												'RMS':np.nan,
												'centDist':np.nan, 'centAngle':np.nan}, index=[0])

			# add this trial summary to the master dataframe for all trials
			if 'allTrials_summarized' not in locals():
				allTrials_summarized = trialSummary.copy()
			else:
				allTrials_summarized = pd.concat([allTrials_summarized, trialSummary], join='outer', ignore_index=True)

	### Write to text files
	gazeCalibration_colOrder = ['trial', 'ptIdx', 'col', 'row', 'trial_ts', 'task_ts', 'gaze_ts',
					'worldFrame', 'confidence',
					'world_gazeX', 'world_gazeY',
					'border_gazeX', 'border_gazeY',
					'calibGrid_gazeX', 'calibGrid_gazeY',
					'distance', 'angle']
	gazeCalibration_df[gazeCalibration_colOrder].to_csv(join(calibDir, 'gazeData_calibration.tsv'), sep='\t', index=False, float_format='%.3f')
	summary_colOrder = ['trial', 'ptIdx', 'percentValid',
						'centX', 'centY', 'centDist', 'centAngle', 'RMS']
	allTrials_summarized[summary_colOrder].to_csv(join(calibDir, 'calibrationSummary.tsv'), sep='\t', index=False, float_format='%.3f')

	### Plot the results
	plotCalibrationGaze(gazeCalibration_df, condition, calibDir)
	plotCalibrationSummary(allTrials_summarized, condition, calibDir)



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


def plotCalibrationGaze(gazeCalibration_df, condition, outputDir):
	"""
	plot all the gazepts for each calibration trial
	"""
	gridImg = mpimg.imread(calibGrid_path)

	# axis formatting
	matplotlib.rc('ytick', labelsize=20)
	matplotlib.rc('xtick', labelsize=20)
	fig = plt.figure(figsize=(16,8))
	fig.suptitle(condition, fontsize=20, fontweight='bold')

	### GazePts on calib grid
	ax = fig.add_subplot(121)
	ax.axis("off")
	ax.imshow(gridImg, cmap='Greys_r', alpha=0.3)		# background img
	ax.scatter(gazeCalibration_df.calibGrid_gazeX, gazeCalibration_df.calibGrid_gazeY,
				s=60, alpha=0.74, edgecolor='k', c=gazeCalibration_df.ptIdx, cmap='Vega20b')

	# set axis limits
	ax.set_ylim(-250, 1250)
	ax.set_xlim(-250, 1250)
	ax.invert_yaxis()

	### Gaze pts on Polar Plot
	ax2 = fig.add_subplot(122, polar=True)
	ax2.set_ylim(0,5)
	ax2.set_yticks([1,2,3])
	ax2.yaxis.set_ticklabels(['1$^\circ$ ', '2$^\circ$ ', '3$^\circ$ '])		# for degree symbol

	# plot gaze pts relative to center
	ax2.scatter(np.deg2rad(gazeCalibration_df['angle'].astype(float)),
							gazeCalibration_df['distance'].astype(float),
							s=150, edgecolor='black', c=gazeCalibration_df.ptIdx, cmap='Vega20b', alpha=.74)

	# put circle at center for reference
	ax2.scatter(0,0, s=2000, facecolor='black', alpha=0.4)
	ax2.spines['polar'].set_visible(False)

	### save
	plt.tight_layout()
	plt.savefig(join(outputDir, 'calibrationPlot_raw.pdf'))
	plt.close()


def plotCalibrationSummary(calibSummary_df, condition, outputDir):
	"""
	plot the summary of gaze calibration for this subject
	"""
	gridImg = mpimg.imread(calibGrid_path)

	# axis formatting
	matplotlib.rc('ytick', labelsize=20)
	matplotlib.rc('xtick', labelsize=20)
	fig = plt.figure(figsize=(16,8))
	fig.suptitle((condition + ' Summary'), fontsize=20, fontweight='bold')

	### Summary plot on calibration grid
	ax = fig.add_subplot(121)
	ax.axis("off")
	ax.imshow(gridImg, cmap='Greys_r', alpha=0.3)

	# centroid location
	ax.scatter(calibSummary_df.centX, calibSummary_df.centY, s=60, c=calibSummary_df.ptIdx, cmap='Vega20b')

	# rms as circle enclosing centroid location
	ax.scatter(calibSummary_df.centX, calibSummary_df.centY,
				s=1000*calibSummary_df.RMS,
				c=calibSummary_df.ptIdx,
				edgecolor='none',
				cmap='Vega20b', alpha=0.5)

	# draw connecting lines
	cmap = plt.cm.get_cmap('Vega20b')
	for p in sorted(calibSummary_df.ptIdx):
		thisPt = calibSummary_df[calibSummary_df.ptIdx == p]

		# figure out the x,y of this calibration point
		p = p-1
		col = p % 5 + 1
		row = np.floor(np.true_divide(p,5))+1
		idealLocation = ((1000/6)*col, (1000/6)*row)

		# plot a line connecting everything
		thisColor = cmap((p)/25)
		xs = [thisPt.centX, idealLocation[0]]
		ys = [thisPt.centY, idealLocation[1]]
		ax.plot(xs, ys, color=thisColor, lw=1)

	ax.set_ylim(-250,1250)
	ax.set_xlim(-250,1250)
	ax.invert_yaxis()

	#### Polar Plot
	ax2 = fig.add_subplot(122, polar=True)
	ax2.set_ylim(0,5)
	ax2.set_yticks([1,2,3])
	ax2.yaxis.set_ticklabels(['1$^\circ$ ', '2$^\circ$ ', '3$^\circ$ '])		# for degree symbol
	ax2.scatter(np.deg2rad(calibSummary_df['centAngle'].astype(float)),
							calibSummary_df['centDist'].astype(float),
							s=150,
							edgecolor='black',
							c=calibSummary_df['ptIdx'],
							cmap='Vega20b',
							alpha=.74)
	# rms
	ax2.scatter(np.deg2rad(calibSummary_df['centAngle'].astype(float)),
							calibSummary_df['centDist'].astype(float),
							s=1500*calibSummary_df.RMS,
							edgecolor='none',
							c=calibSummary_df['ptIdx'],
							cmap='Vega20b',
							alpha=.5)
	ax2.scatter(0,0, s=2000, facecolor='black', alpha=.4)  # put circle at center for reference
	ax2.spines['polar'].set_visible(False)

	### save
	plt.tight_layout()
	plt.savefig(join(outputDir, 'calibrationPlot_summary.pdf'))
	plt.close()


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
