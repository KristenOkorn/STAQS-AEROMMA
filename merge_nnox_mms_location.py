# -*- coding: utf-8 -*-
"""
Created on Wed Dec  6 20:21:49 2023

Merge NNOX O3 & NO2 data with MMS - lat, lon, alt

@author: okorn
"""

# import libraries
import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta

#first do loop for each pod location
#need to pluck out just the lat/lon pairs that are relevant to each pod location
locations = ['AFRC','TMF','Caltech','Whittier','Redlands']
latitudes = [34.95991,34.38189,34.13685,33.97676,34.05985]
longitudes = [-117.88107,-117.67809,-118.12608,-118.03032,-117.14573]

for n in range(len(locations)):
    
    #get an empty dataframe for each pod location
    MMS = pd.DataFrame()
    
    #------------------------------------------------------------
    #First load in the MMS data
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
        
    #------------------------------------------------------------
    #load in the ISAF data - already in csv format
    ISAFfilePath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\NNOX_NO2_O3.csv'
       
    #load in the file
    NNOX = pd.read_csv(ISAFfilePath,index_col=0)
    
    #make sure the index is a datetime
    NNOX.index = pd.to_datetime(NNOX.index, format='%Y-%m-%d %H:%M:%S')
        
    #------------------------------------------------------------
    #merge the MMS and ISAF data
    merge = pd.merge(MMS,NNOX,left_index=True, right_index=True)
        
    #------------------------------------------------------------
    #come up with lat/lon bounds - try 1km total
    #near LA - 1km = 1/111 deg lat, so 1/222 on either side
    #near LA - 1km = 1/85 deg lon, so 1/170 on either side
    
    min_lat_bound = latitudes[n] - (1/222)
    max_lat_bound = latitudes[n] + (1/222)
    
    min_lon_bound = longitudes[n] - (1/170)
    max_lon_bound = longitudes[n] + (1/170)
        
    #Filter the df to just include matching lat/lon
    data = merge[
    (merge['latitude'] >= min_lat_bound) & (merge['latitude'] <= max_lat_bound) &
    (merge['longitude'] >= min_lon_bound) & (merge['longitude'] <= max_lon_bound)
    ]
    
    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\NNOX Outputs\\'
    #save out the final (raw) data
    savePath = os.path.join(Spath,'NNOX_NO2_O3_{}.csv'.format(locations[n]))
    data.to_csv(savePath)
