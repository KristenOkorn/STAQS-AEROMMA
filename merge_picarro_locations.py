# -*- coding: utf-8 -*-
"""
Created on Thu May 23 20:52:33 2024

Load in the AEROMMA DC-8 Picarro data & match it to each of our pod locations

Edited 2/5/2025 to include 3D wind in output file

@author: okorn
"""

# import libraries
import pandas as pd
import os
from datetime import datetime
from tkinter.filedialog import askdirectory

#Prompt user to select folder for analysis
path = askdirectory(title='Select Folder for analysis').replace("/","\\")

#get one large dataframe to save all our Picarro data into
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

#------------------------------------------------------------
#now load in the MMS data

#get an empty dataframe for the MMS data
MMS = pd.DataFrame()
    
#load in the MMS data
MMSpath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\MMS\\R0 (newer)'
    
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
    temp = temp[['TIME_START',' G_LAT', ' G_LONG', ' G_ALT', ' U', ' V', ' W']]
        
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
    
#------------------------------------------------------------
#merge the MMS and Picarro data
merge = pd.merge(MMS,PICARRO,left_index=True, right_index=True)

#------------------------------------------------------------
#now match to each pod location

#need to pluck out just the lat/lon pairs that are relevant to each pod location
locations = ['AFRC','TMF','Caltech','Whittier','Redlands']
latitudes = [34.95991,34.38189,34.13685,33.97676,34.05985]
longitudes = [-117.88107,-117.67809,-118.12608,-118.03032,-117.14573]

#come up with lat/lon bounds - try 1km total
#near LA - 1km = 1/111 deg lat, so 1/222 on either side
#near LA - 1km = 1/85 deg lon, so 1/170 on either side

for n in range(len(locations)):

    min_lat_bound = latitudes[n] - (1/222)
    max_lat_bound = latitudes[n] + (1/222)

    min_lon_bound = longitudes[n] - (1/170)
    max_lon_bound = longitudes[n] + (1/170)
    
    data = merge[
    (merge['latitude'] >= min_lat_bound) & (merge['latitude'] <= max_lat_bound) &
    (merge['longitude'] >= min_lon_bound) & (merge['longitude'] <= max_lon_bound)
    ]

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\Picarro CO2 CH4 CO\\'
    #save out the final (raw) data
    savePath = os.path.join(Spath,'Picarro_CH4_CO2_{}.csv'.format(locations[n]))
    data.to_csv(savePath)
