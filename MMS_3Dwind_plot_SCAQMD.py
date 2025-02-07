# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 11:31:56 2025

Combining with plotting to make wind roses
Load in each of the SCAQMD HCHO sites & merge with MMS

Requires the lat/lon of each SCAQMD site
@author: okorn
"""

# import libraries
import pandas as pd
import os
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

#get the list of SCAQMD locations
locations = ['St Anthony','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park']
latitudes = [33.9185, 33.89011, 33.87049, 33.83718, 33.82494, 33.81917, 33.80229, 33.78136, 33.78199, 33.78607]
longitudes = [-118.40796, -118.4016, -118.3129, -118.33148, -118.26844, -118.21152, -118.22021, -118.21363, -118.26758, -118.2864]

#------------------------------------------------------------
#first load in the MMS data

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

for n in range(len(locations)): 
    #-------------------------------------
    #now load in the SCAQMD data for each site
    scaqmdPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\SCAQMD Data'
    #get the filename for the pod
    scaqmdfilename = "{}.csv".format(locations[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    scaqmdfilepath = os.path.join(scaqmdPath, scaqmdfilename)
    scaqmd = pd.read_csv(scaqmdfilepath,index_col=0)  
    # Replace '--' with NaN in values column
    scaqmd['HCHO'] = scaqmd['HCHO'].replace('--', np.nan)
    #Convert values from string to float
    scaqmd['HCHO'] = scaqmd['HCHO'].astype(float)
    #remove any negatives
    scaqmd = scaqmd[scaqmd.iloc[:, 0] >= 0]
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    scaqmd.index = pd.to_datetime(scaqmd.index,errors='coerce')
    #Change the pollutant column name
    scaqmd.columns.values[0] = 'SCAQMD HCHO'

    #get the data into UTC (from PDT)
    scaqmd.index += pd.to_timedelta(7, unit='h')

    #------------------------------------------------------------
    #merge the MMS and SCAQMD data
    merge = pd.merge(MMS,scaqmd,left_index=True, right_index=True)

    #------------------------------------------------------------
    #now match to each scaqmd location

    #come up with lat/lon bounds - try 1km total
    #near LA - 1km = 1/111 deg lat, so 1/222 on either side
    #near LA - 1km = 1/85 deg lon, so 1/170 on either side
    
    min_lat_bound = latitudes[n] - (1/222)
    max_lat_bound = latitudes[n] + (1/222)

    min_lon_bound = longitudes[n] - (1/170)
    max_lon_bound = longitudes[n] + (1/170)
    
    #Filter the df to just include matching lat/lon
    data = merge[(merge['latitude'] >= min_lat_bound) | (merge['latitude'] <= max_lat_bound) & ((merge['longitude'] >= min_lon_bound) & (merge['longitude'] <= max_lon_bound))]

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\SCAQMD Data\\SCAQMD MMS\\'
    #save out the final (raw) data
    savePath = os.path.join(Spath,'SCAQMD_MMS_{}.csv'.format(locations[n]))
    data.to_csv(savePath)
    
    #------------------------------------------------------------
    
    #figure out how many days we have - for how many subplots
    num_unique_days = len(np.unique(data.index.date))
    #also get the list of them to split by
    unique_days_list = np.unique(data.index.date).tolist()
    
    # Create a dictionary to store DataFrames for each unique day
    split_dataframes = {}

    #Split the DataFrame based on unique days
    for day in unique_days_list:
        day_data = data[data.index.date == day]
        split_dataframes[day] = day_data
    
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(num_unique_days, 1, figsize=(4, 4 * num_unique_days),subplot_kw={'projection':'polar'})
    
    # If there is only one subplot, make it a list to handle indexing
    if num_unique_days == 1:
        axs = [axs]

    for k, (day, df) in enumerate(split_dataframes.items()):
        #extract daily components from vectors
        speed = np.sqrt(df[' U']**2 + df[' V']**2)
        direction = np.arctan2(df[' V'], df[' U'])  
        w_color = df[' W']  # Assuming 'w' is the vertical wind component
        
        #normalize color scaling for w values over full dataset
        norm = plt.Normalize(vmin=data[' W'].min(), vmax=data[' W'].max()) 
    
        #try converting to degrees for troubleshooting
        direction_degrees = np.degrees(direction)
        #now get between 0 and 360
        direction_degrees = (direction_degrees + 360) % 360
        #now convert degrees back to radians
        direction_radians = np.radians(direction_degrees) 
    
        #scatter this day's data
        sc = axs[k].scatter(direction_radians, speed, c=w_color, norm=norm)
     
        #add a colorbar for the vertical component
        cbar = plt.colorbar(sc, ax=axs[k],pad=0.1)
        cbar.set_label('Vertical Wind Speed (m/s)')
 
        #Add a title with the date to each subplot
        axs[k].set_title('{}'.format(day), y=1.1)  # Adjust the vertical position (0 to 1)
       
        # Set the font size of the tick labels
        axs[k].tick_params(axis='both', labelsize=12)
        
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.4, top=0.9, bottom=0.05)  # You can adjust the value as needed
    #Add an overall title
    fig.suptitle('Daily Wind Roses - {}'.format(locations[n]), fontweight='bold')
    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\MMS Outputs\\'
    
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'WindRose_HCHO_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)