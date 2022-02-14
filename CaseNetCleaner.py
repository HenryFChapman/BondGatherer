import pandas as pd
import numpy as np
import os
import shutil

from bondAnalysis import getBondAnalysis


def getCaseInfo(itemFilePath):
	#Derive Case Number
	filePathList = itemFilePath.split("\\")
	courtNumber = filePathList[-2].split(" - ")[1]
	fileNumber = filePathList[-2].split(" - ")[0]

	fileCourtNumbers = []
	fileCourtNumbers.append(fileNumber)
	fileCourtNumbers.append(courtNumber)

	return fileCourtNumbers


def cleanCaseHeader(itemFilePath):
	caseHeader = pd.read_csv(itemFilePath, encoding = 'utf-8')
	caseHeader = caseHeader.set_axis(['Index', 'Information', 'Data','moreInformation', 'moreData'], axis = 1, )

	informationList = caseHeader['Information'].tolist()
	moreInformationList = caseHeader['moreInformation'].tolist()

	informationList.extend(moreInformationList)

	dataList = caseHeader['Data'].tolist()
	moreDataList = caseHeader['moreData'].tolist()
	dataList.extend(moreDataList)

	newCaseHeader = pd.DataFrame()
	newCaseHeader['Information'] = informationList
	newCaseHeader['Data'] = dataList

	newCaseHeader = newCaseHeader.dropna(how='all')

	newCaseHeader['File #'] = getCaseInfo(itemFilePath)[0]
	newCaseHeader['Case #'] = getCaseInfo(itemFilePath)[1]

	return newCaseHeader


def cleanDocketEntry(itemFilePath):
	docketEntry = pd.read_csv(itemFilePath, encoding = 'utf-8', index_col = 0)
	docketEntry = docketEntry.dropna(how='all')
	
	docketEntry = docketEntry.set_axis(['Date', 'Blank', 'EventSummary','EventSummaryDummy', 'Notes', "Blank2"], axis = 1, )

	docketEntry[docketEntry["Date"]==""] = np.NaN
	docketEntry = docketEntry.fillna(method='ffill')
	#docketEntry = docketEntry.sort_index(ascending=False)
	docketEntry = docketEntry[['Date', 'EventSummary', 'Notes']]

	docketEntry['Proper Index'] = docketEntry.index
	docketEntry['Date'] = pd.to_datetime(docketEntry['Date'])
	docketEntry = docketEntry.sort_values(['Date', 'Proper Index'], ascending = (True))

	docketEntry['File #'] = getCaseInfo(itemFilePath)[0]
	docketEntry['Case #'] = getCaseInfo(itemFilePath)[1]
	
	return docketEntry


def getJudge(dataframe):
	dataframe = dataframe[dataframe['Information'] == "Judge/Commissioner Assigned:"]
	try:
		judge = dataframe['Data'].tolist()[0]
	except IndexError:
		judge = "None Listed"
	return judge


def cleanEachSimpleCase(oldDirectory, newDirectory):

	if os.path.exists(newDirectory):
		shutil.rmtree(newDirectory)
	os.mkdir(newDirectory)

	tempBondDF = pd.DataFrame()

	for item in os.listdir(oldDirectory):
		itemFilePath = oldDirectory + item

		if os.listdir(oldDirectory) == 0:
			continue

		if "caseHeader" in item:
			tempCaseHeader = cleanCaseHeader(itemFilePath)
			tempJudge = getJudge(tempCaseHeader)
			tempCaseHeader.to_csv(newDirectory + "caseHeader.csv", encoding = 'utf-8')

		if "docketEntries" in item:

			tempDocketEntry = cleanDocketEntry(itemFilePath)
			tempBondDF = getBondAnalysis(tempDocketEntry)
			tempDocketEntry.to_csv(newDirectory + "docketEntries.csv", encoding = 'utf-8')

	tempBondDF['Judge'] = tempJudge

	return tempBondDF

def dataCleaner(casesToClean):

	masterDirectory = "CaseNetFolders\\"
	cleanedDirectory = "CleanedCases\\"

	allBonds = pd.read_csv("AllBonds.csv")

	listOfBondDFs = []
	listOfBondDFs.append(allBonds)

	for i, row in casesToClean.iterrows():
		
		oldDirectory = masterDirectory + row['CombinedName'] + "\\"
		newDirectory = cleanedDirectory + row['CombinedName'] + "\\"
		tempBondDF = cleanEachSimpleCase(oldDirectory, newDirectory)

		if len(tempBondDF.index) != 0:
			listOfBondDFs.append(tempBondDF)

	#masterBondDF = pd.DataFrame()
	masterBondDF = pd.concat(listOfBondDFs)

	masterBondDF.to_csv("AllBonds.csv", index = False)