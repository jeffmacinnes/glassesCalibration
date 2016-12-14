from __future__ import division
import os
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import json
from os.path import join, dirname


### Configuration Settings
# set up paths
scriptDir = dirname(os.path.realpath(__file__))
EXP_dir = dirname(scriptDir)

calibLogDir = join(EXP_dir, 'data', 'calibrationLogs')
dataDir = join(EXP_dir, 'data')

trialDur = 3000			# duration of each trial in ms
trialWin = (500,2500)	# window within each trial with usable data
pixPerDeg = 166.66		# number of pixels in calibration grid for every 1 deg of visual angle
maxValidPts = int((trialWin[1]-trialWin[0])/1000 * 25)	# calculate number of datapts to expect under ideal conditions

def getDistance(x1,y1,x2,y2):
	# calculate vector distance between two points, return distance in terms of visual angle
	xDist = x2-x1
	yDist = y2-y1
	distance = (np.sqrt(xDist**2 + (yDist**2)))/pixPerDeg
	return distance

def getAngle(x1,y1,x2,y2):
	# calculate vector angle between two points
	xDist = x2-x1
	yDist = (y2-y1)
	return 360-np.rad2deg(np.arctan2(yDist,xDist))

def processCalibrationData(condition):
	""" 
	Take the raw calibration mapped data and align it with the calibration task timepoints. 

	Output will be a csv with calibration data restricted to the relevant time windows for each trial
	"""

	### Figure out the timestamp of the first frame for this subj/condition 
	f = open(join(dataDir, condition, 'output/firstFrame.txt'), 'r')
	startingFrame = int(f.read())
	f.close()

	### Load raw calibration data and create new columns with timestamps relative to task
	calibData = pd.read_table(join(dataDir, condition, 'output/calibrationMapping.txt'))
	taskStartTime = float(calibData.vidTS[calibData.Frame == startingFrame])
	calibData.loc[:, 'taskTS'] = calibData.vidTS-taskStartTime

	### Load the calibration log listing time and order of calibration points
	calibLog = pd.read_table(join(calibLogDir, (condition + '.txt')))
	calibGridDims = (calibLog.col.max(), calibLog.row.max())

	### Loop through each calibration point
	for i in range(calibLog.shape[0]):
		# each pt will be a Series object with values for Col, Row, and Time
		thisPt = calibLog.iloc[i]

		# get trial start time for this pt
		trialStart = thisPt.time

		# figure out the index location of this point (L->R, Top->Bottom)
		ptIdx = (thisPt.row-1)*calibGridDims[0] + thisPt.col

		# Isolate the calibration data for this pt
		trialData = calibData[(calibData.taskTS > trialStart) & (calibData.taskTS <= (trialStart + trialDur))]

		# Add column of timestamps relative to trial onset
		trialData.loc[:, 'trialTS'] = trialData.taskTS - trialStart

		# Isolate the trial data to timepts within the desired window
		trialData = trialData[(trialData.trialTS > trialWin[0]) & (trialData.trialTS <= trialWin[1])]
		if trialData.shape[0] > 0:
			# add info about the calibration point to the dataframe
			trialData['col'] = thisPt.col
			trialData['row'] = thisPt.row
			trialData['ptIdx'] = ptIdx

			# calculate distance/angle from ideal
			idealLocation = ((1000/6)*thisPt.col, (1000/6)*thisPt.row)
			trialData.loc[:, 'distance'] = trialData.apply(lambda d:  getDistance(idealLocation[0], 
																					idealLocation[1], 
																					d['calib_X'], 
																					d['calib_Y']), axis=1)
			trialData.loc[:, 'angle'] = trialData.apply(lambda d:  getAngle(idealLocation[0], 
																					idealLocation[1], 
																					d['calib_X'], 
																					d['calib_Y']), axis=1)
			
			# drop datapts where the distance is more than 5 deg (vis angle)
			trialData = trialData[trialData["distance"] < 5]

			### Summarize this trial #################################
			# calulate percent valid datapts
			percentValid = trialData.shape[0]/maxValidPts

			# calculate centroid coords (mean gaze X,Y in calib coordinates)
			centroidX = np.mean(trialData.calib_X)
			centroidY = np.mean(trialData.calib_Y)

			# calculate distance and angle from ideal for centroid
			centDist = getDistance(idealLocation[0], idealLocation[1], centroidX, centroidY)
			centAngle = getAngle(idealLocation[0], idealLocation[1], centroidX, centroidY)

			# calculate dist from centroid for each datapt
			distFromCentroid = trialData.apply(lambda d: getDistance(centroidX, 
																	centroidY, 
																	d['calib_X'], 
																	d['calib_Y']), axis=1)

			# calculate RMS (square root of mean distance squared)
			RMS = np.sqrt(np.sum(np.square(distFromCentroid)) * (1/distFromCentroid.shape[0]))

			## write this data to a seperate text file
			trialSummary = pd.DataFrame({'ptIdx':ptIdx,
											'percentValid':percentValid,
											'centX': centroidX, 'centY':centroidY,
											'RMS':RMS, 
											'centDist':centDist, 'centAngle':centAngle}, index=[0])


			# add this trial data to the master
			if i == 0:
				allTrials = trialData.copy()
				allTrials_summarized = trialSummary.copy()
			else:
				allTrials = pd.concat([allTrials, trialData], join='outer', ignore_index=True)
				allTrials_summarized = pd.concat([allTrials_summarized, trialSummary], join='outer', ignore_index=True)
	allTrials.to_csv(join(dataDir, condition, 'output/calibrationProcessed.csv'), index=False, sep='\t', float_format='%.2f')
	allTrials_summarized.to_csv(join(dataDir, condition, 'output/calibrationSummarized.csv'), index=False, sep='\t', float_format='%.2f')

	################ PLOTTING ############################
	### Raw Calibration Pts
	# Write plots for this data (datapts on calibration grid AND combined datapts on )
	calibGrid = join(EXP_dir, 'referenceGrids/calibrationGrid.jpg')
	gridImg = mpimg.imread(calibGrid)

	matplotlib.rc('ytick', labelsize=20) 
	matplotlib.rc('xtick', labelsize=20) 
	fig = plt.figure(figsize=(16,8))
	fig.suptitle(condition, fontsize=20, fontweight='bold')

	# Calib Plot
	ax = fig.add_subplot(121)
	ax.axis("off")
	ax.imshow(gridImg, cmap='Greys_r', alpha=0.3)

	ax.scatter(allTrials.calib_X, allTrials.calib_Y, s=60, alpha=0.74, c=allTrials.ptIdx, cmap='Set1')
	ax.set_ylim(-250,1250)
	ax.set_xlim(-250,1250)
	ax.invert_yaxis()

	# Polar Plot
	ax2 = fig.add_subplot(122, polar=True)
	ax2.set_ylim(0,5)
	ax2.set_yticks([1,2,3])
	ax2.yaxis.set_ticklabels(['1$^\circ$ ', '2$^\circ$ ', '3$^\circ$ '])		# for degree symbol
	ax2.scatter(np.deg2rad(allTrials['angle'].astype(float)), 
							allTrials['distance'].astype(float), 
							s=150, 
							edgecolor='black', 
							c=allTrials['ptIdx'], 
							cmap='Set1', 
							alpha=.74)
	ax2.scatter(0,0, s=2000, facecolor='black', alpha=.4)  # put circle at center for reference
	ax2.spines['polar'].set_visible(False)
	
	# save
	plt.tight_layout()
	plt.savefig(join(dataDir, condition, 'output/calibrationPlots_raw.pdf'))


	### Summarized Calibration Pts
	summary_df = allTrials_summarized.copy()
	fig = plt.figure(figsize=(16,8))
	fig.suptitle(condition, fontsize=20, fontweight='bold')

	### Calib Plot
	ax = fig.add_subplot(131)
	ax.axis("off")
	ax.imshow(gridImg, cmap='Greys_r', alpha=0.3)

	# centroid location
	ax.scatter(summary_df.centX, summary_df.centY, s=60, c=summary_df.ptIdx, cmap='Set1')

	# rms
	ax.scatter(summary_df.centX, summary_df.centY, 
				s=1000*summary_df.RMS, 
				c=summary_df.ptIdx, 
				edgecolor='none',
				cmap='Set1', alpha=0.5)

	# draw connecting lines
	cmap = plt.cm.get_cmap('Set1')
	for p in sorted(summary_df.ptIdx):
		thisPt = summary_df[summary_df.ptIdx == p]

		# figure out the x,y of this calibration point
		p = p-1
		col = p % 5 + 1
		row = np.floor(np.true_divide(p,5))+1
		idealLocation = ((1000/6)*col, (1000/6)*row)

		# plot a line connecting everything
		thisColor = cmap(np.true_divide(p+1,25))
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
	ax2.scatter(np.deg2rad(summary_df['centAngle'].astype(float)), 
							summary_df['centDist'].astype(float), 
							s=150, 
							edgecolor='black', 
							c=summary_df['ptIdx'], 
							cmap='Set1', 
							alpha=.74)
	# rms
	ax2.scatter(np.deg2rad(summary_df['centAngle'].astype(float)), 
							summary_df['centDist'].astype(float), 
							s=1500*summary_df.RMS, 
							edgecolor='none', 
							c=summary_df['ptIdx'], 
							cmap='Set1', 
							alpha=.5)
	ax2.scatter(0,0, s=2000, facecolor='black', alpha=.4)  # put circle at center for reference
	ax2.spines['polar'].set_visible(False)

	# save
	#plt.tight_layout()
	plt.savefig(join(dataDir, condition, 'output/calibrationPlots_summarized.pdf'))




if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'condition', help='Condition to analyze (e.g. "j_0deg"')
	args = parser.parse_args()

	processCalibrationData(args.condition)