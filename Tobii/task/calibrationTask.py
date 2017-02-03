import os
import sys
import time
import pygame
import itertools
from random import shuffle

### EXP vars
trial_dur = 3;
cols = rows = ['one', 'two', 'three', 'four', 'five']			# define col, row locations
numDict = {'one':1, 'two':2, 'three':3, 'four':4, 'five':5}

# create randomized row, col pairings
pairings = []
for p in itertools.product(cols, rows):
	pairings.append(p)
shuffle(pairings)

# start log file
f = open('log.txt', 'w')
f.write('\t'.join(['col', 'row', 'time']) + '\n')

# initialize pygame window
pygame.init()
red = 255, 0, 0
green = 0, 255, 0
size = 650, 650
screen = pygame.display.set_mode(size)

# Load the start image
startImg = pygame.image.load("startImage.jpg")

# Show start screen (red screen for 3 sec, then Luuka)
keepGoing = True
displayStart = time.time()
count = 3
while keepGoing:
	curTime = time.time()
	if curTime-displayStart < 3:
		screen.fill(red)
	else:
		screen.blit(startImg, (0,0))
		trialStart = time.time();			# record start time of Luuka appearing
		keepGoing = False

	pygame.display.flip()



s = raw_input('Press Enter to start calibration')

# Loop through each coordinate pairing
for p in pairings:
	
	# say col, write log
	os.system(('say ' + p[0]))
	f.write(str(numDict[p[0]]) + '\t')
	time.sleep(.5);

	# say row, write log
	os.system(('say ' + p[1]))
	f.write(str(numDict[p[1]]) + '\t')

	# write timestamp to log
	f.write('%i' % ((time.time()-trialStart)*1000) + '\n')	# write the time that the instructions finish

	# pause 
	time.sleep(trial_dur)

f.close()

