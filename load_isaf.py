# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 12:33:13 2023

Load in ISAF HCHO data from AEROMMA

@author: okorn
"""

# import libraries
import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
from tkinter.filedialog import askdirectory

#Prompt user to select folder for analysis
path = askdirectory(title='Select Folder for analysis').replace("/","\\")

#get one large dataframe to save all our data into
ISAF = pd.DataFrame()

#Get the list of files from this directory
from os import listdir
from os.path import isfile, join
fileList = [f for f in listdir(path) if isfile(join(path, f))]
#loop through each file
for i in range(len(fileList)):

    #Create full file path for reading file
    filePath = os.path.join(path, fileList[i])
    
    with open(filePath, 'r') as file:
        first_line = file.readline()#Read the first line
        skip=first_line[0:2]
 
    #load in the file
    temp = pd.read_csv(filePath,skiprows=int(skip)-1,header=0)
    
    #get the initial date from the filename
    year = fileList[i][22:26]
    month = fileList[i][26:28]
    day = fileList[i][28:30]
    date = datetime.strptime('{}-{}-{}'.format(year,month,day), "%Y-%m-%d")
    
    #convert seconds past midnight to HH:MM:SS
    temp['datetime'] = date + pd.to_timedelta(temp['Time_Start'], unit='s')

    #clean up the dataframe
    del temp['Time_Start'], temp[' CH2O_ISAF_precision']
    
    #make the datetime the index
    temp = temp.set_index('datetime')
    
    #drop negatives
    temp = temp[~(temp < 0).any(axis=1)]
    
    #append to the overall dataframe
    ISAF = ISAF.append(temp)
    
#save out to csv
savePath = os.path.join(path,'ISAF_HCHO.csv')
ISAF.to_csv(savePath,index=True)