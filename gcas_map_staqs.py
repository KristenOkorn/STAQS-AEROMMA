# -*- coding: utf-8 -*-
"""
Created on Wed Nov  1 13:40:20 2023

@author: okorn

Plot location data for pods & other variables - GCAS
"""

#import libraries
import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
from tkinter.filedialog import askdirectory
import netCDF4 as nc

#import mapping library
import cartopy.crs as ccrs
import cartopy.feature as cf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates


#Prompt user to select folder for analysis
path = askdirectory(title='Select Folder for analysis').replace("/","\\")

#Get the list of files from this directory
from os import listdir
from os.path import isfile, join
fileList = [f for f in listdir(path) if isfile(join(path, f))]

#need to pluck out just the lat/lon pairs that are relevant to each pod location
locations = ['AFRC','TMF','Caltech','Whittier','Redlands']
latitudes = [34.95991,34.38189,34.13685,33.97676,34.05985]
longitudes = [-117.88107,-117.67809,-118.12608,-118.03032,-117.14573]
colors = ['b','g','r','c','m']

#Do a separate plot for each day 
for i in range(len(fileList)):
    
    #Create full file path for reading file
    filePath = os.path.join(path, fileList[i])

    f = nc.Dataset(filePath, 'r')

    #print the list of base items for our reference
    #print(f.variables.keys())

    #pull out the variables we need
    time = f.variables['time'][:] #assuming secs past midnight
    no2 = f.variables['no2_differential_slant_column'][:]
    alt = f.variables['aircraft_altitude'][:]
    cloud_glint_flag = f.variables['cloud_glint_flag'][:]
    lat_bounds = f.variables['lat_bounds'][:]
    lon_bounds = f.variables['lon_bounds'][:]

    #handle 2 different file naming conventions
    if fileList[i].find('LaRC') != -1:
        #get the initial date from the filename
        year = fileList[i][23:27]
        month = fileList[i][27:29]
        day = fileList[i][29:31]
    else:
        #get the initial date from the filename
        year = fileList[i][22:26]
        month = fileList[i][26:28]
        day = fileList[i][28:30]
    
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
    df['NO2']  = np.nan
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
    
    #get the min & max across each row to make plotting simpler
    max_lat = np.nanmin(min_lat_bound, axis=1)
    min_lat = np.nanmin(min_lat_bound, axis=1)
    max_lon = np.nanmin(min_lon_bound, axis=1)
    min_lon = np.nanmin(min_lon_bound, axis=1)
    
    #close out of this file
    f.close()

    # %% lat/lon map (colored by time)
    
    fig4 = plt.figure(4)
    
    projection = ccrs.Mercator()
    #projection = ccrs.Mercator(central_longitude=180) #else try this

    ax4 = plt.axes(projection=projection)
    
    #Add stock image with custom land and ocean colors
    ax4.stock_img()
    ax4.background_patch.set_facecolor('tan')  # Set land color
    ax4.add_feature(cf.OCEAN, edgecolor='none', facecolor='lightblue')  # Set ocean color
    
    ax4.add_feature(cf.COASTLINE)
    ax4.add_feature(cf.BORDERS)
    
    plate = ccrs.PlateCarree()

    #first add the GCAS data - lat/lon minimums first
    ax4.scatter(max_lon, max_lat, c='gray', s=3, transform=plate,label='GCAS Tracks')

    #now add the GCAS data - lat/lon maximums second
    #ax4.scatter(max_lon, max_lat, c='gray', s=5, transform=plate)
    
    #next add the pod data so it sits on top
    for k in range(len(locations)):
        ax4.scatter(longitudes[k], latitudes[k],c=colors[k], s=20, transform=plate, label='{}'.format(locations[k]))
    
    #Calculate the buffer values
    x_buffer = .2 * (max(max_lon) - min(max_lon))
    y_buffer = .2 * (max(max_lat) - min(max_lat))

    #Adjust the extent based on the buffer
    ax4.set_extent([min(max_lon) - x_buffer, max(max_lon) + x_buffer, min(max_lat) - y_buffer, max(max_lat) + y_buffer], crs=ccrs.PlateCarree())
    
    fig4.tight_layout()
    
    #Adding a title to fig4
    fig4.suptitle('GCAS - {}/{}/{}'.format(year,month,day), y=0.95)  # Adjust the vertical position (0 to 1)
    
    #add a legend
    ax4.legend(loc='upper right')

    #Display the plot
    plt.show()
    
    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\GCAS NO2 Outputs\\'
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'GCAS_map_{}_{}_{}'.format(year,month,day))
    # Save the figure to a filepath
    fig4.savefig(savePath)
