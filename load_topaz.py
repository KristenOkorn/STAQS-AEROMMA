# -*- coding: utf-8 -*-
"""
Created on Fri Feb 16 16:06:32 2024

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
TOPAZ = pd.DataFrame()

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
        skip=first_line[24:26]
 
    #load in the file
    temp = pd.read_csv(filePath,skiprows=int(skip)-1,header=0,delim_whitespace=True)
    
    #Remove leading and trailing whitespaces from column names
    temp.columns = temp.columns.str.strip()
    
    #combine the date & time columns
    temp['datetime'] = temp['Date,UTC'].astype(str) + temp['Time,UTC'].astype(str)
    
    #convert from str to datetime
    temp['datetime'] = pd.to_datetime(temp['datetime'], format="%Y%m%d%H%M%S", errors='coerce')

    #clean up the dataframe
    del temp['Date,UTC']
    del temp['Time,UTC']
    del temp['Date,MST']
    del temp['Time,MST']
    
    #make the datetime the index
    temp = temp.set_index('datetime')
    
    #append to the overall dataframe
    TOPAZ = TOPAZ.append(temp)
    
#save out to csv
savePath = os.path.join(path,'topaz.csv')
TOPAZ.to_csv(savePath,index=True)