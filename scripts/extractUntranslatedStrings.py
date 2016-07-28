#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Get strings that need trnslation from an .xlf file and output as a text file

Example: python extractUntranslatedStrings.py "/Users/benchang/Documents/source/ExtensisSource/release/Suitcase14.2.0/FontManagement/Shared Code/Localization"

"""

import sys, os, unittest, codecs, platform

def getFileContent(filePath):
	"""
	Read in the file content.
	"""
	try:
		logFile = open(filePath, 'r')
		fileContent = logFile.read()
		logFile.close()
	except:
		fileContent = None
		
	return fileContent

def writeToFile(filePath, fileContent, append=False):
	try:
		if append:
			outputFile = open(filePath, 'a')
		else:
			outputFile = open(filePath, 'w')
		outputFile.write(fileContent)
		outputFile.close()
	except:
		a = 1

def main():
	localizationFolder = sys.argv[0].split('Localization')[0] + 'Localization'
	fileNames = os.listdir(localizationFolder)
	for fileName in fileNames:
		if fileName.endswith(".xlf"):
			filePath = localizationFolder + os.sep + fileName
			# read in the .xlf file
			fileContent = getFileContent(filePath)
			
			# get the untranslated strings
			untranslatedStrings = ""
			stringBlocks = fileContent.split("</trans-unit>")
			for stringBlock in stringBlocks:
				if "<target/>" in stringBlock:
					for stringLine in stringBlock.split("\n"):
						if "<source" in stringLine:
							theString = stringLine.split(">")[1]
							theString = theString.split("<")[0]
							untranslatedStrings += theString + "\n\n"
							
			# output file
			outputFile = filePath[:-3] + "txt"
			writeToFile(filePath=outputFile, fileContent=untranslatedStrings)
			print "Generated: " + outputFile

if __name__=="__main__":
	main()