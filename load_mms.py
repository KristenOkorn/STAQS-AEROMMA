# -*- coding: utf-8 -*-
"""
Created on Fri Oct  3 10:48:31 2025

Load the MMS data into a standalone csv

@author: okorn
"""
import pandas as pd
import os
from datetime import datetime

#get an empty dataframe for each pod location
MMS = pd.DataFrame()

#------------------------------------------------------------
#First load in the MMS data
MMSpath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\MMS\\R0'

#Get the list of files from this directory
from os import listdir
from os.path import isfile, join
MMSfileList = [f for f in listdir(MMSpath) if isfile(join(MMSpath, f))]

#iterate over each file in the main folder
for i in range(len(MMSfileList)):

    #Create full file path for reading file
    MMSfilePath = os.path.join(MMSpath, MMSfileList[i])

    with open(MMSfilePath, 'r') as file:
        first_line = file.readline()#Read the first line
        skip=first_line[0:2]
 
    #load in the file
    temp = pd.read_csv(MMSfilePath,skiprows=int(skip)-1,header=0)
    
    #get the initial date from the filename
    year = MMSfileList[i][20:24]
    month = MMSfileList[i][24:26]
    day = MMSfileList[i][26:28]
    date = datetime.strptime('{}-{}-{}'.format(year,month,day), "%Y-%m-%d")
    
    #just keep the relevant columns
    temp = temp[['TIME_START',' G_LAT', ' G_LONG', ' G_ALT',' U', ' V', ' W']]
    
    #rename the columns
    temp.rename(columns={'TIME_START': 'datetime', ' G_LAT': 'latitude', ' G_LONG':'longitude',' G_ALT':'altitude'}, inplace=True)
    
    # Convert seconds to HH:MM:SS
    temp['datetime'] = pd.to_datetime(temp['datetime'], unit='s', origin=date)
    
    #drop the fractional seconds
    temp['datetime'] = temp['datetime'].dt.floor('1S')
    
    #make the datetime the index
    temp = temp.set_index('datetime')
    
    #fix the lat/lon - periods not converted in
    temp['latitude'] = temp['latitude']/100000
    temp['longitude'] = temp['longitude']/100000
    
    #also convert the wind
    temp[' U'] = temp[' U']/10
    temp[' V'] = temp[' V']/10
    temp[' W'] = temp[' W']/10
    
    #append this date to the overall MMS dataframe
    MMS = MMS.append(temp)

#write it out to a csv
savePath = os.path.join(MMSpath,'MMS.csv')
MMS.to_csv(savePath)