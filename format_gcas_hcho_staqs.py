# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 14:34:45 2024

Updating load nc GCAS files for HCHO data

@author: okorn
"""

# import libraries
import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
from tkinter.filedialog import askdirectory
import netCDF4 as nc

#Prompt user to select folder for analysis
path = askdirectory(title='Select Folder for analysis').replace("/","\\")

#Get the list of files from this directory
from os import listdir
from os.path import isfile, join
fileList = [f for f in listdir(path) if isfile(join(path, f))]

#first do loop for each pod location
#need to pluck out just the lat/lon pairs that are relevant to each pod location
locations = ['AFRC','TMF','Caltech','Whittier','Redlands']
latitudes = [34.95991,34.38189,34.13685,33.97676,34.05985]
longitudes = [-117.88107,-117.67809,-118.12608,-118.03032,-117.14573]

for n in range(len(locations)):
    
    #get an empty dataframe for each pod location
    data = pd.DataFrame()

    #iterate over each file in the main folder
    for i in range(len(fileList)):
    
        #Create full file path for reading file
        filePath = os.path.join(path, fileList[i])
    
        f = nc.Dataset(filePath, 'r')
    
        #print the list of base items for our reference
        #print(f.variables.keys())
    
        #pull out the variables we need
        time = f.variables['time'][:] #assuming secs past midnight
        no2 = f.variables['hcho_vertical_column_below_aircraft'][:]
        alt = f.variables['aircraft_altitude'][:]
        #cloud_glint_flag = f.variables['cloud_glint_flag'][:]
        lat_bounds = f.variables['lat_bounds'][:]
        lon_bounds = f.variables['lon_bounds'][:]
    
        #handle 2 different file naming conventions
        if fileList[i].find('LaRC') != -1:
            #get the initial date from the filename
            year = fileList[i][24:28]
            month = fileList[i][28:30]
            day = fileList[i][30:32]
        # else:
        #     #get the initial date from the filename
        #     year = fileList[i][22:26]
        #     month = fileList[i][26:28]
        #     day = fileList[i][28:30]
        
        date = datetime.strptime('{}-{}-{}'.format(year,month,day), "%Y-%m-%d")
    
        #convert seconds past midnight to HH:MM:SS
        hours, remainder = divmod(time, 3600)
        minutes, seconds = divmod(remainder, 60)
        seconds = np.round(seconds) #round seconds the nearest whole number
    
        #Convert to datetime array
        my_datetime = []
        for h, m, s in zip(hours.flat, minutes.flat, seconds.flat):
            delta = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
            my_datetime.append(date + delta)    
        my_datetime = np.array(my_datetime)
    
        #save all the data we extracted as a dataframe, with a NaN column for NO2
        df = pd.DataFrame(index=my_datetime)
        df['HCHO']  = np.nan
        df['altitude'] = alt
        #df['cloud_glint_flag'] = np.nan
        
        #unmask the bounds - 3D data
        unmasked_lat = lat_bounds.filled(np.nan)
        unmasked_lon = lon_bounds.filled(np.nan)
        
        #get an array of the bounds for each (0 = 3D axis)
        max_lat_bound = np.max(unmasked_lat, axis=0)
        min_lat_bound = np.min(unmasked_lat, axis=0)
        max_lon_bound = np.max(unmasked_lon, axis=0)
        min_lon_bound = np.min(unmasked_lon, axis=0)
        
        #Check for matching latitudes within the bounds
        match_lat = np.where((latitudes[n] >= min_lat_bound) & (latitudes[n] <= max_lat_bound))[0]
        #Check for matching longitudes within the buffer
        match_lon = np.where((longitudes[n] >= min_lon_bound) & (longitudes[n] <= max_lon_bound))[0]
        #Find the intersection of matching latitudes and longitudes
        match_indices = np.intersect1d(match_lat, match_lon)
        
        if match_indices.size != 0:
            #Get row and column indices
            rows, columns = np.unravel_index(match_indices, min_lat_bound.shape)
            
            #Now add in the matching NO2 data for each pod
            for k in range(len(rows)):
                df.loc[my_datetime[k], 'HCHO'] = no2[rows[k],columns[k]]
                #And save the matching cloud glint data
                #df.loc[my_datetime[k], 'cloud_glint_flag'] = cloud_glint_flag[rows[k],columns[k]]
        
        #close out of this file
        f.close()
        
        #concatenate data from this loop into the overall dataframe
        data = data.append(df)
    
    #drop missing values
    data = data.dropna()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\GCAS HCHO Outputs\\'
    #save out the final (raw) data
    savePath = os.path.join(Spath,'GCAS_HCHO_{}.csv'.format(locations[n]))
    data.to_csv(savePath)