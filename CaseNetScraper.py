from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import NoSuchElementException   
import time
from bs4 import BeautifulSoup as bs
import pandas as pd
import os
import shutil

from CaseNetCleaner import dataCleaner

def getJustFileNumbers():

	listOfScrapedCases = os.listdir("CaseNetFolders\\")
	listOfFileNumbers = []

	for folder in listOfScrapedCases:
		tempFileNumber = folder.split(" - ")[0]
		listOfFileNumbers.append(tempFileNumber)

	return listOfFileNumbers

def lookUpCaseStatus(receivedCases):

	#Loading WebDriver
	options = FirefoxOptions()
	options.headless = True
	driver = webdriver.Firefox(options = options)

	listOfScrapedCases = getJustFileNumbers()

	receivedCases = receivedCases[~receivedCases['File #'].isin(listOfScrapedCases)].reset_index()

	for i, row in receivedCases.iterrows():

		if "\\" in row['Case #']:
			continue
		if "/" in row['Case #']:
			continue

		if "-0" in row['Case #']:
			tempCaseNumber = row['Case #'][:-3]
		else:
			tempCaseNumber = row['Case #']

		tempFolder = "CaseNetFolders\\" + str(int(row['File #'])) + " - " +  tempCaseNumber
		
		print(row['File #'])
		print(row['Case #'])
		print(tempFolder)

		if os.path.exists(tempFolder):
			shutil.rmtree(tempFolder)
		os.mkdir(tempFolder)

		url = "https://www.courts.mo.gov/casenet/cases/header.do?inputVO.caseNumber=" + tempCaseNumber + "&inputVO.courtId=CT16"

		#Loading CaseNet
		driver.get(url)

		content = driver.page_source
		while "429 Too Many Requests" in content:
			time.sleep(60)
			driver.get(url)
			content = driver.page_source

		try:
			table = driver.find_element_by_xpath("/html/body/table/tbody/tr[2]/td/table/tbody/tr[1]/td/table")
			tempCaseHeader  = pd.read_html(table.get_attribute('outerHTML'))[0]
			tempCaseHeader.to_csv(tempFolder + "\\caseHeader.csv")

			docketEntries = driver.find_element_by_xpath('/html/body/table/tbody/tr[1]/td/table/tbody/tr[2]/td/table/tbody/tr[2]/td/form/center/table/tbody/tr/td/a[3]/img')
			docketEntries.click()
			time.sleep(5)

			docketEntries = driver.find_element_by_xpath('//*[@id="respondToForm"]/table')
			docketEntriesTable  = pd.read_html(docketEntries.get_attribute('outerHTML'))[0]
			docketEntriesTable.to_csv(tempFolder + "\\docketEntries.csv")

		except NoSuchElementException:
			time.sleep(5)

		time.sleep(5)

	driver.close()

#Move Complete Results to New Folder
def moveCompleteCases(receivedCases):

	#Old Directory
	caseNetFolders = "CaseNetFolders\\"

	#Create Complete Cases Directory
	completeCaseNet = "CompleteCaseNet\\"

	if os.path.exists(completeCaseNet):
		os.mkdir(completeCaseNet)

	listOfScrapedCases = os.listdir(caseNetFolders)

	for caseFile in listOfScrapedCases:

		#remove empty cases
		if len(os.listdir(caseNetFolders + caseFile)) == 0:
			shutil.rmtree(caseNetFolders + caseFile)

		#remove cases with 0 in them
		elif " - 0" in caseFile:
			shutil.rmtree(caseNetFolders + caseFile)

		elif "-0" not in caseFile:
			shutil.move(caseNetFolders + caseFile, completeCaseNet + caseFile)

def getAdditionalCaseStatus(receivedCases):
	
	#Loading WebDriver
	options = FirefoxOptions()
	options.headless = False
	driver = webdriver.Firefox(options = options)

	#Cache Previous Results
	listOfScrapedCases = os.listdir("CaseNetFolders\\")

	#CompletedCases
	listOfCompletedCases = os.listdir("ComplicatedCases")

	for scrapedCase in listOfScrapedCases:
		tempFileNumber = scrapedCase.split(" - ")[0]

		#Get Base Case
		baseCase = scrapedCase.split(" - ")[1].split("-0")[0]
		numberOfCases = int(scrapedCase.split(" - ")[1].split("-0")[1])

		tempFolder = "ComplicatedCases\\" + str(tempFileNumber) + " - " +  baseCase
		folder = str(tempFileNumber) + " - " +  baseCase

		if folder in listOfCompletedCases:
			continue

		if os.path.exists(tempFolder):
			shutil.rmtree(tempFolder)
		os.mkdir(tempFolder)

		#loop through completed cases
		for i in range(0, numberOfCases+1):

			tempCaseNumber = ""

			if i == 0:
				tempCaseNumber = baseCase
			else:
				tempCaseNumber = baseCase + "-" + str(i).zfill(2)

			url = "https://www.courts.mo.gov/casenet/cases/header.do?inputVO.caseNumber=" + tempCaseNumber + "&inputVO.courtId=CT16"
			driver.get(url)
			content = driver.page_source

			while "429 Too Many Requests" in content:
				time.sleep(60)
				driver.get(url)
				content = driver.page_source

			try:
				table = driver.find_element_by_xpath("/html/body/table/tbody/tr[2]/td/table/tbody/tr[1]/td/table")
				tempCaseHeader  = pd.read_html(table.get_attribute('outerHTML'))[0]
				tempCaseHeader.to_csv(tempFolder + "\\caseHeader"+ " - " + str(i)+".csv")

				docketEntries = driver.find_element_by_xpath('/html/body/table/tbody/tr[1]/td/table/tbody/tr[2]/td/table/tbody/tr[2]/td/form/center/table/tbody/tr/td/a[3]/img')
				docketEntries.click()
				time.sleep(5)

				docketEntries = driver.find_element_by_xpath('//*[@id="respondToForm"]/table')
				docketEntriesTable  = pd.read_html(docketEntries.get_attribute('outerHTML'))[0]
				docketEntriesTable.to_csv(tempFolder + "\\docketEntries"+ " - " + str(i)+".csv")

			except NoSuchElementException:
				time.sleep(5)

			time.sleep(5)

	driver.close()

def getNewestFile(weeklyUpload):

	#Initializes Blank List 
	allDates = []

	#Loops through the Weekly Data Drop Folder
	for item in os.listdir(weeklyUpload):

		#Pulls the Date from Each File in the Folder
		date = int(item.split("_")[1])

		#Appends it to a list
		allDates.append(date)

	#Removes all the duplicates
	allDates = list(set(allDates))

	#Sorts the List without Duplicates
	allDates.sort()

	#Grabs the most recent file
	mostRecent = str(allDates[-1])

	#Returns that most recent file. 
	return mostRecent

def makeDirectoryOfCases(caseNetFoldersDirectory, spreadsheetTitle):

	#caseNetFoldersDirectory = "CaseNetFolders\\"

	fileNumber = []
	caseNumber = []
	hasContents = []
	folderList = []
	combinedName = []

	#get list of cases
	for folder in os.listdir(caseNetFoldersDirectory):
		tempFileNumber = folder.split(" - ")[0]
		fileNumber.append(tempFileNumber)
		tempCaseNumber = folder.split(" - ")[1]
		caseNumber.append(tempCaseNumber)

		#get length of folder
		tempLength = os.listdir(caseNetFoldersDirectory + folder)
		if len(tempLength) == 0:
			hasContents.append("Empty")
		else:
			hasContents.append("Scraped")

		folderList.append(caseNetFoldersDirectory + folder)
		combinedName.append(folder)

	#initialize dataframe
	caseDataFrame = pd.DataFrame()
	caseDataFrame['File #'] = fileNumber
	caseDataFrame['Case #'] = caseNumber
	caseDataFrame['HasContents'] = hasContents
	caseDataFrame['FolderPath'] = folderList
	caseDataFrame['CombinedName'] = combinedName

	caseDataFrame.to_csv(spreadsheetTitle, index = False)
	return caseDataFrame

def dataScraper():

	#This Section of Code Grabs the Cases That Haven't Been Scraped Yet
	weeklyUpload = "H:\\Units Attorneys and Staff\\01 - Units\\DT Crime Strategies Unit\\Weekly Update\\"
	caseDirectory = weeklyUpload + "CaseNo_" + getNewestFile(weeklyUpload) + "_1800.CSV"
	caseNumbers = pd.read_csv(caseDirectory, error_bad_lines = False, warn_bad_lines = False)

	caseNumbers = caseNumbers.dropna(subset = ['Case #'])
	lookUpCaseStatus(caseNumbers)


	#Clean Cases That Have Contents and Aren't Cleaned
	rawCasesDataFrame = makeDirectoryOfCases("CaseNetFolders\\", "rawCasesDirectory.csv")
	cleanCasesDataFrame = makeDirectoryOfCases("CleanedCases\\", "cleanedCases.csv")

	cleanedFileNumbers = cleanCasesDataFrame['File #'].tolist()
	casesToClean = rawCasesDataFrame[~rawCasesDataFrame['File #'].isin(cleanedFileNumbers)]
	casesToClean = casesToClean[casesToClean['HasContents']=="Scraped"]
	dataCleaner(casesToClean)

dataScraper()