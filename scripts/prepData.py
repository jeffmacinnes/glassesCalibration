import os
from os.path import join, dirname
import sys
import shutil
import gzip
import tobii_data_process

# set up paths
scriptDir = dirname(os.path.realpath(__file__))
expDir = dirname(scriptDir)

# mapping between the Tobii assigned name and the condition
dirs = {'ibgdpow':'j_0deg_down',
		'dgvwzek':'k_15deg_R',
		'fxfhoaq':'k_10deg_R',
		'ufydkxg':'k_5deg_R',
		'mgx7vgj':'k_5deg_L',
		'fjmyadr':'k_10deg_L',
		'pt7hits':'k_15deg_L',
		'su2lnph':'k_0deg'}


def prepRawData(curDir, newDir):
	"""
	Copy participant raw data to new directory and unzip the JSON file
	"""
	print 'prepping ' + newDir
	if os.path.isdir(join(expDir, 'data', newDir)):
		print 'Directory named ' + newDir + ' already exists. Try again...'
	else:
		os.makedirs(join(expDir, 'data', newDir))

		# copy the participant data to the new directory
		for f in ['fullstream.mp4', 'livedata.json.gz']:
			srcFile = join(expDir, 'data/raw_data', curDir, 'segments/1', f)
			dstDir = join(expDir, 'data', newDir)
			shutil.copy(srcFile, dstDir)

		# unzip the json data
		gzFile = join(expDir, 'data', newDir, 'livedata.json.gz')
		print gzFile
		unzip_dest = gzFile.split('.gz')[0]
		with gzip.open(gzFile) as infile:
			with open(unzip_dest, 'w+') as outfile:
				for line in infile:
					outfile.write(line)

		# process the JSON file
		tobii_data_process.process(unzip_dest, 0)



if __name__ == '__main__':
	# loop through all pairings specified in dictionary
	for key in dirs:
		curDir = key
		newDir = dirs[key]
		prepRawData(curDir, newDir)

