import os
import sys
import cv2
import argparse
import json
import time
import numpy as np
import pandas as pd
from os.path import join
from bisect import bisect_left


"""
USAGE:
	python calibrationTest.py <pathToSourceDir> <backgroundImage> <startImage>


Before looping through source video:
	- find keypoints,desc on background
	- find keypoints, desc on calibration grid
	- find transformation from background to grid


For each frame of the source video:
	- write a new frame of output video with gaze superimposed on source video
	- find the poster
		- run a check to see if there was a good match?
	- map the gaze coordinates from source video to background coords.
		- write this data to master dataframe
		- write a new frame of ouput video with gaze superimposed on background
	- map the gaze coords from background to calibration grid
		- write this data to master dataframe
		- write a new frame of output video with gaze superimposed on calibration grid

outputs:
	- original untouched source video
	- source video with gaze
	- poster video with gaze
	- calibration video with gaze
	- csv with cols for timestamp; source X,Y; background X,Y; grid X,Y; 
"""


def prepGazeData(gaze_file, frame_dims):
	"""
	Load the gaze data csv (created from tobii_data_process.py - Shariq) and
	format it for use throughout this script
	"""

	df = pd.read_csv(gaze_file)
	df = df[~df.vts_time.isnull()]			# remove data recorded before video started

	# grab only the desired values
	gaze_val = df['gaze_pos_val'].values
	gaze_x = df['gaze_pos_x'].values * frame_dims[0]	# convert from % to frame pixel coords
	gaze_y = df['gaze_pos_y'].values * frame_dims[1] 
	vts = df['vts_time'].values / 1000.   # convert vts from microseconds to ms
	vts = vts-vts[0] 					  # make timestamps relative to first timestamp

	# create new dataframe
	gaze_dict = {'gaze_val':gaze_val, 'gaze_x': gaze_x, 'gaze_y': gaze_y, 'vts': vts}
	gaze_df = pd.DataFrame(gaze_dict)
	return gaze_df


def findClosest(myList, searchValue):
	"""
	Assumes myList is sorted. Returns index location in myList where you'll find the
	closest value to searchValue.

	If two numbers are equally close, return the index of the smallest number.
	"""
	pos = bisect_left(myList, searchValue)
	if pos == 0:
		return myList[0]
	if pos == len(myList):
		return myList[-1]
	before = myList[pos - 1]
	after = myList[pos]
	if after - searchValue < searchValue - before:
		return pos
	else:
		return pos-1


def getGaze(gaze_df, index):
	"""
	Return the gaze values in frame coords from the desired index location
	"""
	if gaze_df.gaze_val[index] == 0:
		gazeX = np.round(gaze_df.gaze_x[index])
		gazeY = np.round(gaze_df.gaze_y[index])
		return gazeX, gazeY
	else:
		return None, None

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

def mapCoords2D(coords, transform2D):
	"""
	Will map the supplied coords to a new coordinate system using the supplied transformation matrix
	"""
	coords = np.array(coords).reshape(-1,1,2)
	mappedCoords = cv2.perspectiveTransform(coords, transform2D)
	mappedCoords = np.round(mappedCoords.ravel())

	return mappedCoords[0], mappedCoords[1] 



def map2calibration(srcDir, bgFile, calibFile, startFile):
	"""
	Map the gaze data from the source video coordinate system to the 
	background image, and ultimately to the calibration grid itself.

	inputs:
		srcDir: path to source data directory
		bgFile: path to background image
		calibFile: path to calibration grid image
		startFile: path to start image used to signal onset of task
	"""

	### Configurate Settings ####################
	# SIFT feature detection settings
	featureDetect = cv2.SIFT()


	### setup inputs  ###########################
	# prep source data and video
	gazeData = join(srcDir, 'livedata.csv')
	vidFile = join(srcDir, 'fullstream.mp4')
	srcVid = cv2.VideoCapture(vidFile)
	totalFrames = srcVid.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
	srcVidSize = (int(srcVid.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)), int(srcVid.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)))
	srcFPS = srcVid.get(cv2.cv.CV_CAP_PROP_FPS)

	# task start cue
	referenceDir, tmp = os.path.split(calibFile)
	print referenceDir
	startImg = cv2.imread(startFile)
	startImg = cv2.cvtColor(startImg, cv2.COLOR_BGR2GRAY)

	# background and calibration grid reference images
	bgImg = cv2.imread(bgFile)
	bgImgColor = bgImg.copy()				# store a color copy of the image
	bgImg = cv2.cvtColor(bgImg, cv2.COLOR_BGR2GRAY)
	bgObjSize = (30, 20)     				# height, width in desired real-world units. MAKE INTO A COMMAND LINE INPUT

	calibImg = cv2.imread(calibFile)
	calibImgColor = calibImg.copy()
	calibImg = cv2.cvtColor(calibImg, cv2.COLOR_BGR2GRAY)

	# prep gaze data file
	gaze_df = prepGazeData(gazeData, srcVidSize)
	maxGazeTS = gaze_df['vts'].max()
	print 'max time (vts): %s' % str(maxGazeTS)


	### setup outputs ###########################
	outputDir = join(srcDir, 'output')
	if not os.path.isdir(outputDir):
		os.makedirs(outputDir)
	outputFile = join(outputDir, 'calibrationMapping.txt')

	# output videos
	vidCodec = cv2.cv.CV_FOURCC(*'mp4v')

	vidOut_orig_fname = join(outputDir, 'source_orig.m4v')
	vidOut_orig = cv2.VideoWriter()
	vidOut_orig.open(vidOut_orig_fname, vidCodec, srcFPS, srcVidSize, True)

	vidOut_gaze_fname = join(outputDir, 'source_gaze.m4v')
	vidOut_gaze = cv2.VideoWriter()
	vidOut_gaze.open(vidOut_gaze_fname, vidCodec, srcFPS, srcVidSize, True)

	vidOut_bg_fname = join(outputDir, 'bg_gaze.m4v')
	vidOut_bg = cv2.VideoWriter()
	vidOut_bg.open(vidOut_bg_fname, vidCodec, srcFPS, (bgImg.shape[1], bgImg.shape[0]), True)

	vidOut_calibGrid_fname = join(outputDir, 'calibGrid_gaze.m4v')
	vidOut_calibGrid = cv2.VideoWriter()
	vidOut_calibGrid.open(vidOut_calibGrid_fname, vidCodec, srcFPS, (calibImg.shape[1], calibImg.shape[0]), True)

	# output dataframe
	colNames = ['vidTS', 'Frame', 'src_X', 'src_Y', 
			'bg_X', 'bg_Y', 'calib_X', 'calib_Y']
	output_df = pd.DataFrame(columns=colNames)


	### Find mapping between background and calibration grid images ##################
	# find keypoints, descriptors for the start image
	startImg_kp, startImg_des = featureDetect.detectAndCompute(startImg, None)
	print 'Task Start Cue: found %s keypoints' % len(startImg_kp)

	# find keypoints, descriptors for each image
	bgImg_kp, bgImg_des = featureDetect.detectAndCompute(bgImg, None)
	calibImg_kp, calibImg_des = featureDetect.detectAndCompute(calibImg, None)
	print 'Background Image: found %s keypoints' % len(bgImg_kp)
	print 'Calibration Grid: found %s keypoints' % len(calibImg_kp)

	# find matching points, and filter to find best ones
	calibImg_pts, bgImg_pts = findMatches(calibImg_kp, calibImg_des, bgImg_kp, bgImg_des)
	if len(calibImg_pts) > 4:
		print 'Successfully matched background image and calibration grid'
	else:
		print 'Failed to find sufficient match points between background image and calibration grid'
		sys.exit()

	# find transformation mapping between the 2 coordinate systems
	bg2calib_transform, mask = cv2.findHomography(bgImg_pts.reshape(-1,1,2), calibImg_pts.reshape(-1,1,2), cv2.RANSAC, 5.0)
	calib2bg_transform = cv2.invert(bg2calib_transform)
	calib2bg_transform = calib2bg_transform[1]

	# # test
	w, h, c = bgImgColor.shape
	warpedCalib = cv2.warpPerspective(calibImg, calib2bg_transform, (h,w))
	cv2.imwrite(join(outputDir, 'grid2bg_warp.jpg'), warpedCalib);


	### Loop through Source Video ##################
	# start and end time of srcVideo
	vidEnd = 999	# end time (sec) (huge value if you just want to use all frames)
	framesToUse = np.arange(0, vidEnd*int(srcFPS), 1)				# list of frames to use 
	foundStart = False

	# loop over frames
	frameCounter = 0
	while srcVid.isOpened():
		# read the next frame of the source video
		ret, frame = srcVid.read()
		
		# get the timestamp in ms of this frame
		frameTime = srcVid.get(cv2.cv.CV_CAP_PROP_POS_MSEC)
		
		if (ret == True) and (frameCounter in framesToUse):

			# create copy of original color frame
			origFrame = frame.copy()

			# write untouched frame to the orig output video
			vidOut_orig.write(origFrame)

			# convert the frame to grayscale
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

			# find the features on this frame
			frame_kp, frame_des = featureDetect.detectAndCompute(frame, None)
			print 'found %s features on frame %s' %(len(frame_kp), frameCounter)

			# look for the start image if not already found
			if not foundStart:
				startPts, framePts = findMatches(startImg_kp, startImg_des, frame_kp, frame_des)

				if (startPts is not None):
					if len(startPts) > 25:
						print "found %s start cue matches on frame %s" %(len(startPts), frameCounter)
						print "FIRST FRAME: %s" %(frameCounter)
						cv2.imwrite(join(outputDir, ('firstFrame_' + str(frameCounter).zfill(4) + '.jpg')), origFrame)
						f = open(join(outputDir, 'firstFrame.txt'), 'w')
						f.write(str(frameCounter))
						f.close()
						foundStart = True

			# find matches between frame and background image
			if len(frame_kp) < 2:
				bgPts = None
			else:
				bgPts, framePts = findMatches(bgImg_kp, bgImg_des, frame_kp, frame_des)

			# check if match was possible
			if (bgPts == None):
				print 'found 0 matches on frame %s' %(frameCounter)

			else:
				print 'found %s matches on frame %s' %(bgPts.shape[0], frameCounter)

				# find transformation mapping between the frame and background image
				bg2frame_transform, mask = cv2.findHomography(bgPts.reshape(-1,1,2), framePts.reshape(-1,1,2), cv2.RANSAC, 5.0)
				frame2bg_transform = cv2.invert(bg2frame_transform)
				frame2bg_transform = frame2bg_transform[1]

				# get the gaze point for this frame
				frameIdx = findClosest(gaze_df['vts'], frameTime)
				frame_gazeX, frame_gazeY = getGaze(gaze_df, frameIdx)

				# check if gaze point is valid. if so, convert to other coord systems
				if (frame_gazeX == None) or (frame_gazeY == None):
					bg_gazeX = bg_gazeY = calib_gazeX = calib_gazeY = np.nan
				
				else:
					# convert from frame to background coords, and from background to calibGrid coords
					bg_gazeX, bg_gazeY = mapCoords2D((frame_gazeX, frame_gazeY), frame2bg_transform)
					calib_gazeX, calib_gazeY = mapCoords2D((bg_gazeX, bg_gazeY), bg2calib_transform)

					# draw circles to output frames for all vids
					cv2.circle(origFrame, (int(frame_gazeX), int(frame_gazeY)), 8, [0,0,255], -2)
					cv2.circle(bgImgColor, (int(bg_gazeX), int(bg_gazeY)), 8, [0,0,255], -2)
					cv2.circle(calibImgColor, (int(calib_gazeX), int(calib_gazeY)), 8, [0,0,255], -2)

				# write output
				thisFrameData = {'vidTS':frameTime, 'Frame':np.int32(frameCounter), 
								'src_X':frame_gazeX, 'src_Y':frame_gazeY,
								'bg_X':bg_gazeX, 'bg_Y':bg_gazeY,
								'calib_X':calib_gazeX, 'calib_Y':calib_gazeY}
				thisFrame_df = pd.DataFrame(data=thisFrameData, index=[0])
				output_df = output_df.append(thisFrame_df, ignore_index=True)
				output_df.to_csv(outputFile, index=False, sep='\t', float_format='%.2f', columns=colNames)


			# write output video
			vidOut_gaze.write(origFrame)
			vidOut_bg.write(bgImgColor)
			vidOut_calibGrid.write(calibImgColor)

		# increment frame counter
		frameCounter += 1
		if (frameCounter > np.max(framesToUse)) or frameCounter >= totalFrames or (frameTime + 2*srcFPS) > maxGazeTS:
			srcVid.release()
			vidOut_orig.release()
			vidOut_gaze.release()
			vidOut_bg.release()
			vidOut_calibGrid.release()
			output_df.to_csv(outputFile, index=False, sep='\t', float_format='%.2f', columns=colNames)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'srcDir', help='Source directory (must contain the fullstream.mp4 and livedata.csv files')
	parser.add_argument(
		'bgImage', help='Background image (filename) on which the calibration grid is mounted')
	parser.add_argument(
		'startImage', help='Start image (filename) used to signal the beginning of the task')
	args = parser.parse_args()

	# set up paths
	scriptDir = dirname(os.path.realpath(__file__))
	expDir = dirname(scriptDir)

	bgFile = join(expDir, 'stimuli/referenceGrids', args.bgImage)
	calibFile = join(expDir, 'stimuli/referenceGrids/calibrationGrid.jpg')
	startFile = join(expDir, 'task', args.startImage)

	startTime = time.time()
	map2calibration(args.srcDir, bgFile, calibFile, startFile)
	endTime = time.time()-startTime
	print 'Computation time: %s seconds' % str(endTime) 