"""
Extract specific frames from video. Save each frame as jpg
"""

import os
import sys
import cv2
import numpy as np 
from os.path import join, dirname


### Config Vars ###############################################
# Inputs
# set up paths
scriptDir = dirname(os.path.realpath(__file__))
expDir = dirname(scriptDir)
dataDir = join(expDir, 'data')

cond = 'j_0deg_A'
vidFile = join(dataDirsrc_di, cond, 'fullstream.mp4')						# source video file

# Outputs
output_dir = join(dataDir, cond, 'frames')
if not os.path.isdir(output_dir):
	os.makedirs(output_dir)


# Settings
vidFPS = 25
vidStart = 7	# start time (sec)
vidEnd = 9	 	# end time (sec)
framesToUse = np.arange(vidStart*vidFPS, vidEnd*vidFPS, 1)				# list of frames to use 
###############################################


# Load Video
vid = cv2.VideoCapture(vidFile)
totalFrames = vid.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
vidSize = (int(vid.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)), int(vid.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)))
fps = vid.get(cv2.cv.CV_CAP_PROP_FPS)

# loop through every frame
frameCounter = 0;
while vid.isOpened():

	# read the next frame of the video
	ret, frame = vid.read()
	if (ret == True) and (frameCounter in framesToUse):

		print 'Frame: ' + str(frameCounter)

		# write the frame
		frame_fname = join(output_dir, ('frame_' + str(frameCounter).zfill(4) + '.jpg'))
		cv2.imwrite(frame_fname, frame)
		#frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	frameCounter += 1
	if frameCounter > np.max(framesToUse):
		vid.release()