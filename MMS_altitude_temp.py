# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 16:27:39 2024

Plot MMS temperature data to determine PBL height

@author: okorn
"""

# import libraries
import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
from tkinter.filedialog import askdirectory
import matplotlib.pyplot as plt

#Prompt user to select folder for analysis
path = askdirectory(title='Select Folder for analysis').replace("/","\\")

#get one large dataframe to save all our data into
METNAV = pd.DataFrame()

#Get the list of files from this directory
from os import listdir
from os.path import isfile, join
fileList = [f for f in listdir(path) if isfile(join(path, f))]

#Initialize a figure
fig, ax = plt.subplots(1, len(fileList), figsize=(15, 5), sharey=True)  # 1 row and n_plots columns

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
    year = fileList[i][20:24]
    month = fileList[i][24:26]
    day = fileList[i][26:28]
    date = datetime.strptime('{}-{}-{}'.format(year,month,day), "%Y-%m-%d")
    
    #convert seconds past midnight to HH:MM:SS
    temp['datetime'] = date + pd.to_timedelta(temp['TIME_START'], unit='s')

    #make the datetime the index
    temp = temp.set_index('datetime')
    
    #append to the overall dataframe
    METNAV = METNAV.append(temp)
    
    #mask to pull out negatives
    temp['T'] = temp['T'].where(temp['T'] >= 0, np.nan)
    temp['G_ALT'] = temp['G_ALT'].where(temp['G_ALT'] >= 0, np.nan)
    
    #remove multipliers
    temp['T'] = temp['T']/100
    temp['G_ALT'] = temp['G_ALT']/10
    
    #now make a subplot for each day
    ax[i].scatter(temp['T'], temp['G_ALT'], label=f'Dataset {i+1}', alpha=0.7, s=1)
    #add date label
    ax[i].set_title('{}'.format(date))
    #all axis labels
    ax[i].set_xlabel('Temperature (K)')
    ax[i].set_ylabel('Altitude (m)')
    #set y-limit to look at assumed boundary layer
    #ax[i].set_ylim(ymin=0, ymax=1000) 
    
#save out to csv
savePath = os.path.join(path,'MMS_full.csv')
METNAV.to_csv(savePath,index=True)