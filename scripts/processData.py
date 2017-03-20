"""
step 2: processing

This script will process data for the calibration task. Make sure to have completed step 1: preprocessing
before starting. Preprocessing scripts vary by glasses model (check the specific glasses manufacturer directory). 

This script assumes preprocessing has been done, and regardless of glasses model, the data has been converted to 
a common format. 

This script will copy the preprocessed data from the ./<manufacturer>/data directory to a new directory in ./data.
The new directory will be named according to subj and condition.

It will loop through every frame of the worldCamera.mp4 video, and try to map the gaze coordinates from the world 
coordinate system, to the border image, to the calibration grid image. 

Output will be stored in a directory called "processed"
Output:
	- world_gaze.mp4:		world video w/ gaze points overlaid
	- border_gaze.mp4:		video of border image w/ gaze points overlaid
	- calibGrid_gaze.mp4:	video of calibration grid w/ gaze point overlaid
	- gazeData_mapped.tsv:	gazeData mapped to all 3 coordinate systems
"""

# python 2/3 compatibility
from __future__ import division
from __future__ import print_function

import os, sys
import shutil
import cv2
import time
import argparse
import json
import numpy as np 
import pandas as pd 
from os.path import join

### configuration vars
border_path = '../referenceGrids/enhancedGrid.jpg'
calibGrid_path = '../referenceGrids/calibrationGrid.jpg'

OPENCV3 = (cv2.__version__.split('.')[0] == '3')
print("OPENCV version " + cv2.__version__)


def copyPreprocessing(preprocessedDir, condition):
	"""
	copy the data from the preprocessing dir to a new dir based on condition name
	"""
	outputDir = join('../data', condition)

	# create dir
	if not os.path.isdir(outputDir):
		os.makedirs(outputDir)

	# copy files
	for f in ['worldCamera.mp4', 'gazeData_world.tsv', 'frame_timestamps.tsv']:
		src = join(preprocessedDir, f)
		shutil.copy(src, outputDir)


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


def projectImage2D(origFrame, transform2D, newImage):
	"""
	Will warp the new Imag according to the supplied transformation matrix and write into the original frame
	"""
	# warp the new image to the video frame
	warpedImage = cv2.warpPerspective(newImage, transform2D, origFrame.T.shape[1:])

	# mask and subtract new image from video frame
	warpedImage_bw = cv2.cvtColor(warpedImage, cv2.COLOR_BGR2GRAY)
	if warpedImage.shape[2] == 4:
		alpha = warpedImage[:,:,3]
		alpha[alpha == 255] = 1 			# create mask of non-transparent pixels
		warpedImage_bw =cv2.multiply(warpedImage_bw, alpha)

	ret, mask = cv2.threshold(warpedImage_bw, 10, 255, cv2.THRESH_BINARY)
	mask_inv = cv2.bitwise_not(mask)
	origFrame_bg = cv2.bitwise_and(origFrame, origFrame, mask=mask_inv)

	# mask the warped new image, and add to the masked background frame
	warpedImage_fg = cv2.bitwise_and(warpedImage[:,:,:3], warpedImage[:,:,:3], mask=mask)
	newFrame = cv2.add(origFrame_bg, warpedImage_fg)

	# return the warped new frame
	return newFrame


def processRecording(condition):
	"""
	process the preprocessed data saved in the directory specifed by 'condition'

	Map the gaze data from the source video coordinate system to the 
	background image, and ultimately to the calibration grid itself.
	"""

	### SetUp inputs/outputs
	dataDir = join('../data', condition)
	
	# create dir to store output of processing
	procDir = join(dataDir, 'processed')
	if not os.path.isdir(procDir):
		os.makedirs(procDir)

	# copy the reference stims into the processed dir
	for f in [border_path, calibGrid_path]:
		shutil.copy(f, procDir)

	# load gaze data
	gazeWorld_df = pd.read_table(join(dataDir, 'gazeData_world.tsv'), sep='\t')

	### Load the border and calibration grid images
	borderImg = cv2.imread(join(procDir, border_path.split('/')[-1]))
	borderImgColor = borderImg.copy()				# store a color copy of the image
	borderImg = cv2.cvtColor(borderImg, cv2.COLOR_BGR2GRAY)

	calibImg = cv2.imread(join(procDir, calibGrid_path.split('/')[-1]))
	calibImgColor = calibImg.copy()
	calibImg = cv2.cvtColor(calibImg, cv2.COLOR_BGR2GRAY)

	### Prep the video data #######################################
	# load the video, get parameters
	vid = cv2.VideoCapture(join(dataDir, 'worldCamera.mp4'))
	if OPENCV3:
		totalFrames = vid.get(cv2.CAP_PROP_FRAME_COUNT)
		vidSize = (int(vid.get(cv2.CAP_PROP_FRAME_WIDTH)), int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT)))
		fps = vid.get(cv2.CAP_PROP_FPS)
		vidCodec = cv2.VideoWriter_fourcc(*'mp4v')
		featureDetect = cv2.xfeatures2d.SIFT_create()
	else:
		totalFrames = vid.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
		vidSize = (int(vid.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)), int(vid.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)))
		fps = vid.get(cv2.cv.CV_CAP_PROP_FPS)
		vidCodec = cv2.cv.CV_FOURCC(*'mp4v')
		featureDetect = cv2.SIFT()

	vidOut_world_fname = join(procDir, 'world_gaze.m4v')
	vidOut_world = cv2.VideoWriter()
	vidOut_world.open(vidOut_world_fname, vidCodec, fps, vidSize, True)

	vidOut_border_fname = join(procDir, 'border_gaze.m4v')
	vidOut_border = cv2.VideoWriter()
	vidOut_border.open(vidOut_border_fname, vidCodec, fps, (borderImg.shape[1], borderImg.shape[0]), True)

	vidOut_calibGrid_fname = join(procDir, 'calibGrid_gaze.m4v')
	vidOut_calibGrid = cv2.VideoWriter()
	vidOut_calibGrid.open(vidOut_calibGrid_fname, vidCodec, fps, (calibImg.shape[1], calibImg.shape[0]), True)

	vidOut_border2world_fname = join(procDir, 'border2World_mapped.m4v')
	vidOut_border2world = cv2.VideoWriter()
	vidOut_border2world.open(vidOut_border2world_fname, vidCodec, fps, vidSize, True)

	### Find mapping between border and calibration grid images ##################
	# find keypoints, descriptors for each image
	borderImg_kp, borderImg_des = featureDetect.detectAndCompute(borderImg, None)
	calibImg_kp, calibImg_des = featureDetect.detectAndCompute(calibImg, None)
	print('Background Image: found {} keypoints'.format(len(borderImg_kp)))
	print('Calibration Grid: found {} keypoints'.format(len(calibImg_kp)))

	# find matching points, and filter to find best ones
	calibImg_pts, borderImg_pts = findMatches(calibImg_kp, calibImg_des, borderImg_kp, borderImg_des)
	if len(calibImg_pts) > 4:
		print('Successfully matched background image and calibration grid')
	else:
		print('Failed to find sufficient match points between background image and calibration grid')
		sys.exit()

	# find transformation mapping between the 2 coordinate systems
	border2calib_transform, mask = cv2.findHomography(borderImg_pts.reshape(-1,1,2), calibImg_pts.reshape(-1,1,2), cv2.RANSAC, 5.0)
	calib2border_transform = cv2.invert(border2calib_transform)
	calib2border_transform = calib2border_transform[1]

	### Loop over video frames #########################################################
	framesToUse = np.arange(235, 10000, 1)
	if totalFrames > framesToUse.max():
		framesToUse = framesToUse[framesToUse <= totalFrames]  	# make sure no attempts on nonexistent frames

	frameProcessing_startTime = time.time()
	frameCounter = 0
	while vid.isOpened():
		# read the next frame of the video
		ret, frame = vid.read()
		
		# check if it's a valid frame
		if (ret==True) and (frameCounter in framesToUse):

			# make copies of the border and calibGrid frames (will be used to write to respective output videos w/ or w/o circles)
			border_frame = borderImgColor.copy()
			calibGrid_frame = calibImgColor.copy()

			# process this frame
			processedFrame = processFrame(frame, frameCounter, borderImg_kp, borderImg_des, featureDetect)

			# if good match between border and this frame
			if processedFrame['foundGoodMatch']:

				# grab the gaze data (world coords) for this frame
				thisFrame_gazeData_world = gazeWorld_df.loc[gazeWorld_df['frame_idx'] == frameCounter]

				# project the border image back into the video as a way to check for good mapping
				border2world_frame = projectImage2D(processedFrame['origFrame'], processedFrame['border2world'], borderImgColor)

				# loop over all gaze data for this frame, translate to different coordinate systems
				for i, gazeRow in thisFrame_gazeData_world.iterrows():
					ts = gazeRow['timestamp']
					frameNum = frameCounter
					conf = gazeRow['confidence']

					# translate normalized gaze data to world pixel coords
					world_gazeX = gazeRow['norm_pos_x'] * processedFrame['frame_gray'].shape[1]
					world_gazeY = gazeRow['norm_pos_y'] * processedFrame['frame_gray'].shape[0]

					# covert from world to border pixel coordinates
					border_gazeX, border_gazeY = mapCoords2D((world_gazeX, world_gazeY), processedFrame['world2border'])

					# convert from border to calibGrid pixel coordinates
					calibGrid_gazeX, calibGrid_gazeY = mapCoords2D((border_gazeX, border_gazeY), border2calib_transform)

					# create dict for this row
					thisRow_df = pd.DataFrame({'gaze_ts': ts, 'worldFrame': frameNum, 'confidence':conf,
							'world_gazeX': world_gazeX, 'world_gazeY': world_gazeY,
							'border_gazeX': border_gazeX, 'border_gazeY': border_gazeY,
							'calibGrid_gazeX': calibGrid_gazeX, 'calibGrid_gazeY': calibGrid_gazeY}, index=[i])

					# append row to gazeMapped_df output
					if 'gazeMapped_df' in locals():
						gazeMapped_df = pd.concat([gazeMapped_df, thisRow_df])
					else:
						gazeMapped_df = thisRow_df

					### Draw gaze circles on frames
					if i == thisFrame_gazeData_world.index.max():
						dotColor = [96, 52, 234]			# pinkish/red
						dotSize = 12
					else:
						dotColor = [168, 231, 86]			# minty green
						dotSize = 8
					cv2.circle(frame, (int(world_gazeX), int(world_gazeY)), dotSize, dotColor, -1)						# world frame
					cv2.circle(border_frame, (int(border_gazeX), int(border_gazeY)),  dotSize, dotColor, -1)				# border frame
					cv2.circle(calibGrid_frame, (int(calibGrid_gazeX), int(calibGrid_gazeY)),  dotSize, dotColor, -1)	# calibGrid frame
			else:
				# if not a good match, just use the original frame for the border2world
				border2world_frame = processedFrame['origFrame']

			# write outputs to video
			vidOut_world.write(frame)
			vidOut_border.write(border_frame)
			vidOut_calibGrid.write(calibGrid_frame)
			vidOut_border2world.write(border2world_frame)

		# increment frame counter
		frameCounter += 1
		if frameCounter > np.max(framesToUse):
			# release all videos
			vid.release()
			vidOut_world.release()
			vidOut_border.release()
			vidOut_calibGrid.release()
			vidOut_border2world.release()

			# write out gaze data
			try:
				colOrder = ['worldFrame', 'gaze_ts', 'confidence',
							'world_gazeX', 'world_gazeY', 'border_gazeX', 'border_gazeY', 'calibGrid_gazeX', 'calibGrid_gazeY']
				gazeMapped_df[colOrder].to_csv(join(procDir, 'gazeData_mapped.tsv'), sep='\t', index=False, float_format='%.3f')
			except:
				print('cound not write gazeData_mapped to csv')
				pass

	endTime = time.time()
	frameProcessing_time = endTime - frameProcessing_startTime
	print('Total time: %s seconds' % frameProcessing_time)
	print('Avg time/frame: %s seconds' % (frameProcessing_time/framesToUse.shape[0]) )



def processFrame(frame, frameNumber, border_kp, border_des, featureDetect):
	"""
	Process a single frame from the world camera
		- try to find match between frame and border image
		- if success, return the mapping
	"""
	fr = {}		# create dict to store info for this frame
	
	# create copy of original frame
	origFrame = frame.copy()
	fr['origFrame'] = origFrame 		# store

	# convert to grayscale
	frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	fr['frame_gray'] = frame_gray

	# try to match the frame and the border image
	try:
		frame_kp, frame_des = featureDetect.detectAndCompute(frame_gray, None)
		print('found {} features on frame {}'.format(len(frame_kp), frameNumber))

		if len(frame_kp) < 2:
			border_matchPts = None
		else:
			border_matchPts, frame_matchPts = findMatches(border_kp, border_des, frame_kp, frame_des)

		# check if matches were found
		try:
			numMatches = border_matchPts.shape[0]

			# if sufficient number of matches....
			if numMatches > 10:
				print('found {} matches on frame {}'.format(numMatches, frameNumber))
				sufficientMatches = True
			else:
				print('Insufficient matches ({}} matches) on frame {}'.format(numMatches, frameNumber))
				sufficientMatches = False

		except:
			print ('no matches found on frame {}'.format(frameNumber))
			sufficientMatches = False
			pass

		fr['foundGoodMatch'] = sufficientMatches

		# figure out homographies between coordinate systems
		if sufficientMatches:
			border2world_transform, mask = cv2.findHomography(border_matchPts.reshape(-1,1,2), frame_matchPts.reshape(-1,1,2), cv2.RANSAC, 5.0)
			world2border_transform = cv2.invert(border2world_transform)

			fr['border2world'] = border2world_transform
			fr['world2border'] = world2border_transform[1]

	except:
		fr['foundGoodMatch'] = False
	
	# return the processed frame
	return fr



if __name__ == '__main__':

	# parse arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('preprocessedDir', help='path to preprocessed data dir')
	parser.add_argument('condition', help='name of the experimental condition (e.g. 101_Tobii_1M_0deg)')
	args = parser.parse_args()

	## error checking
	if not os.path.isdir(args.preprocessedDir):
		print('{} is not a valid preprocessed data dir').format(args.preprocessedDir)
	else:
		## copy the data
		print('copying preprocessed data to {}...'.format(join('data', args.condition)))
		#copyPreprocessing(args.preprocessedDir, args.condition)

		## process the recording
		print('processing the recording...')
		processRecording(args.condition)







