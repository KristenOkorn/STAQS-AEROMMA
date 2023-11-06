# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 14:20:49 2023

Load in Picarro ratio - both raw values & mixing ratios for CO, CO2, C4
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
PICARRO = pd.DataFrame()

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
    
    #Remove leading and trailing whitespaces from column names
    temp.columns = temp.columns.str.strip()
    
    #get the initial date from the filename
    year = fileList[i][35:39]
    month = fileList[i][39:41]
    day = fileList[i][41:43]
    date = datetime.strptime('{}-{}-{}'.format(year,month,day), "%Y-%m-%d")
    
    #convert seconds past midnight to HH:MM:SS
    temp['datetime'] = date + pd.to_timedelta(temp['Time_Start'], unit='s')

    #clean up the dataframe
    del temp['Time_Start']
    
    #make the datetime the index
    temp = temp.set_index('datetime')
    
    #append to the overall dataframe
    PICARRO = PICARRO.append(temp)
    
#save out to csv
savePath = os.path.join(path,'picarro.csv')
PICARRO.to_csv(savePath,index=True)