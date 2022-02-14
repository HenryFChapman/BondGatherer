import os
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt

def extractBondAmount(bondSummary):
	s = [float(s) for s in re.findall(r'-?\d+\.?\d*', bondSummary)]

	if len(s) == 2:
		initialBond = s[0]*(s[1]*.01)
	elif len(s) == 0:
		initialBond = 0
	else:
		initialBond = s[0]
	return initialBond

def constructBondDataFrame(dataframe):

	dataframe['EventSummary'] = dataframe['EventSummary'].str.replace(r',', '')

	initialBondDataFrame = pd.DataFrame()
	fileNumbers = []
	dates = []
	initialBondList = []
	caseNumbers = []

	for i, row in dataframe.iterrows():
		fileNumbers.append(row['File #'])
		dates.append(row['Date'])
		initialBondList.append(extractBondAmount(row['EventSummary']))
		caseNumbers.append(row['Case #'])

	initialBondDataFrame["File #"] = fileNumbers
	initialBondDataFrame['Date'] = dates
	initialBondDataFrame['Date'] = pd.to_datetime(initialBondDataFrame["Date"])
	initialBondDataFrame["Initial Bond"] = initialBondList
	initialBondDataFrame["Initial Bond"] = initialBondDataFrame["Initial Bond"].abs()
	initialBondDataFrame["Case #"] = caseNumbers

	return initialBondDataFrame

def getBondAnalysis(tempDocketEntry):

	#Get Bond Information
	tempBondInformation = tempDocketEntry[tempDocketEntry['Notes'] == "Bond Set"]
	tempBondInformation = tempBondInformation[tempBondInformation['EventSummary'] != 'Bond Set']

	#Get Initial Bond
	initialBond = tempBondInformation.drop_duplicates(subset = 'File #', keep = 'first').reset_index()
	initialBondDataFrame = constructBondDataFrame(initialBond)

	return initialBondDataFrame
