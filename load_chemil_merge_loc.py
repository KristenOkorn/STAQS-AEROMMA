# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 08:04:41 2025

Load chemiluminescense ozone data and match it to each pod location

@author: okorn
"""

# import libraries
import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta

input_dir = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\CL O3'
output_dir = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\CL O3 Outputs'

#create an overarching dataframe
cl = pd.DataFrame()

for filename in os.listdir(input_dir):
    #get the full path name
    filePath = os.path.join(input_dir, filename)
    
    #read from file how many rows to skip at the top
    with open(filePath, 'r') as file:
        first_line = file.readline()#Read the first line
        skip=first_line[0:2]
    #load in the file
    temp = pd.read_csv(filePath,skiprows=int(skip)-1,header=0)
    #Remove leading and trailing whitespaces from column names
    temp.columns = temp.columns.str.strip()
    
    #get the initial date from the filename
    year = filename[18:22]
    month = filename[22:24]
    day = filename[24:26]
    date = datetime.strptime('{}-{}-{}'.format(year,month,day), "%Y-%m-%d")
    
    #convert seconds past midnight to HH:MM:SS
    temp['datetime'] = date + pd.to_timedelta(temp['Time_Start'], unit='s')
    #clean up the dataframe
    del temp['Time_Start']
    #make the datetime the index
    temp = temp.set_index('datetime')
    #drop negatives
    temp = temp[~(temp < 0).any(axis=1)]
    #append to the overall dataframe
    cl = cl.append(temp)
    
#save the overall file to csv
savePath = os.path.join(input_dir,'CL_O3.csv')
cl.to_csv(savePath,index=True)

#------------------------------------------------------
#now match to each location

#get list of locations to loop through
locations = ['AFRC','TMF','Caltech','Whittier','Redlands']
latitudes = [34.95991,34.38189,34.13685,33.97676,34.05985]
longitudes = [-117.88107,-117.67809,-118.12608,-118.03032,-117.14573]

#------------------------------------------------------
#first step - load in the mms data
MMSpath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\MMS\\R0 (newer)'

#overarching dataframe to hold all the MMS data
MMS = pd.DataFrame()

for mmsfilename in os.listdir(MMSpath):
    #get the full path name
    mmsfilePath = os.path.join(MMSpath, mmsfilename)
    
    with open(mmsfilePath, 'r') as file:
        first_line = file.readline()#Read the first line
        skip=first_line[0:2]
     
    #load in the file
    temp = pd.read_csv(mmsfilePath,skiprows=int(skip)-1,header=0)
        
    #get the initial date from the filename
    year = mmsfilename[20:24]
    month = mmsfilename[24:26]
    day = mmsfilename[26:28]
    date = datetime.strptime('{}-{}-{}'.format(year,month,day), "%Y-%m-%d")
        
    #just keep the relevant columns
    temp = temp[['TIME_START',' G_LAT', ' G_LONG', ' G_ALT',' U', ' V', ' W']]
    #rename the columns
    temp.rename(columns={'TIME_START': 'datetime', ' G_LAT': 'latitude', ' G_LONG':'longitude',' G_ALT':'altitude'}, inplace=True)
    #Convert seconds to HH:MM:SS
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

#------------------------------------------------------
#now actually match to the locations

#merge the MMS and ISAF data
merge = pd.merge(MMS,cl,left_index=True, right_index=True)
    
#------------------------------------------------------------
#now match the lat/lon

for n in range(len(locations)):

    #come up with lat/lon bounds - try 1km total
    #near LA - 1km = 1/111 deg lat, so 1/222 on either side
    #near LA - 1km = 1/85 deg lon, so 1/170 on either side
    
    min_lat_bound = latitudes[n] - (5/111)
    max_lat_bound = latitudes[n] + (5/111)
    
    min_lon_bound = longitudes[n] - (5/85)
    max_lon_bound = longitudes[n] + (5/85)
        
    #Filter the df to just include matching lat/lon
    data = merge[
    (merge['latitude'] >= min_lat_bound) & (merge['latitude'] <= max_lat_bound) &
    (merge['longitude'] >= min_lon_bound) & (merge['longitude'] <= max_lon_bound)
    ]
    
    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\CL O3 Outputs\\'
    #save out the final (raw) data
    savePath = os.path.join(Spath,'CL_O3_{}.csv'.format(locations[n]))
    data.to_csv(savePath)