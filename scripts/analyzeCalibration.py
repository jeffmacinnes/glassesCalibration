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
from os.path import join


startImage_path = '../task/startImage.jpg'

def processCalibration(condition):
	"""
	process the calibration data for this condition. 
	"""

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
	print('Searching for task start frame...')
	startFrameNum, startFrame = findStartFrame(join(dataDir, 'worldCamera.mp4'))
	cv2.imwrite(join(calibDir, ('startFrame_' + str(startFrameNum).zfill(4) + '.jpg')), startFrame)
	with open(join(calibDir, 'startFrame.txt'), 'w') as f:
		f.write(str(startFrameNum))


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
