#!/usr/bin/python
#
# prune_archives.py -- removes individual files from local copy if older than CUTOFF_DATE
# minimum requirements: python 3.5 and zip

import subprocess
import logging

from zipfile import ZipFile, Path
from datetime import date


def cmp_zipfile(archive, CUTOFF_DATE=date(2021, 3, 1)):
	"""
	return a set of all the files in the zip archive which are older than CUTOFF_DATE
		- archive should be a zip file of a directory of data files. 
		- The directory and zip file's basenames should be the same
		- CUTOFF_DATE is an optional parameter with a default
	"""
	
	old_files = set()
	# TODO wrap this in an error handling 'try' block
	# TODO add logging of failures and successes
	with ZipFile(archive, 'r') as our_zip:
		for file in Path(our_zip, at=archive.split('.')[0] + '/').iterdir():
			# extract date info from filename convention. ex: 20210430_158732.dat
			year, month, day = file.name[0:4], file.name[4:6], file.name[6:8]
			# python's 'date' object wants integers and no leading zeroes.
			file_date = date(int(year), int(month.lstrip('0')),  int(day.lstrip('0')))
			if file_date < CUTOFF_DATE:
				old_files.add(file.name)
	return old_files


def main():
	""" 
	check both zip archives for old files. 
	If any exist in both, prune them from local copy
	"""
	logging.basicConfig(level=logging.INFO)
	logging.info("Cleaning up old files from local zipped data archives")

# TODO: use arguments instead of hard-coded archive file names
# TODO: '--help' text
	cfht_files = cmp_zipfile('CFHT.ZIP')
	cadc_files = cmp_zipfile('CADC.ZIP')

	# only delete files which appear in both sets (intersection)
	files_to_delete = (cfht_files & cadc_files)
	if files_to_delete:
		# Oh no! There is no ZipFile module member to delete files from an archive.
		# We have to run the zip tool. 'subprocess' skips spawning a new shell, though.
		subprocess.run([
			"zip", 
			"CFHT.ZIP",
			"-d"] +
			["CFHT/" + file for file in files_to_delete]
		)
	else:
		logging.info("No files found that need pruning")
# TODO parse and log results of zip process as returned from subprocess.run()


if __name__ == '__main__':
	main()
