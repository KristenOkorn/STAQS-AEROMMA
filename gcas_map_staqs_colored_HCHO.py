# -*- coding: utf-8 -*-
"""
Created on Wed Nov  1 13:40:20 2023

@author: okorn

GCAS tracks colored by HCHO concentration
with INSTEP concentration overlaid

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
import matplotlib.colors as mcolors


#Prompt user to select folder for analysis
path = askdirectory(title='Select Folder for analysis').replace("/","\\")

#Get the list of files from this directory
from os import listdir
from os.path import isfile, join
fileList = [f for f in listdir(path) if isfile(join(path, f))]

#need to pluck out just the lat/lon pairs that are relevant to each pod location
locations = ['TMF','Whittier','Redlands']#'AFRC','Caltech',
latitudes = [34.38189,33.97676,34.05985]#34.95991,34.13685,
longitudes = [-117.67809,-118.03032,-117.14573]#-117.88107,-118.12608,
pods = ['YPODA2','YPODA7','YPODL5']

#sites & dates where we have data overlapping with GCAS
dates = ['2023-08-22','2023-08-23','2023-08-25']
Whittier_HCHO = [2.04375,2.14523,2.93427]
Whittier_alt = [8663.8766,6726.1166,9049.99255]
TMF_HCHO = [2.04375,2.14523,2.93427]
TMF_alt = [8663.877,6726.1167,9049.9926]
Redlands_HCHO = [2.04375,2.14523,2.93427]
Redlands_alt=[8663.87657,6726.1166,9049.99255]

#Do a separate plot for each day 
for i in range(len(fileList)):

    #Create full file path for reading file
    filePath = os.path.join(path, fileList[i])

    f = nc.Dataset(filePath, 'r')

    #print the list of base items for our reference
    #print(f.variables.keys())

    #pull out the variables we need
    time = f.variables['time'][:] #assuming secs past midnight
    hcho = f.variables['hcho_vertical_column_below_aircraft'][:]
    alt = f.variables['aircraft_altitude'][:]
    #cloud_glint_flag = f.variables['cloud_glint_flag'][:]
    lat_bounds = f.variables['lat_bounds'][:]
    lon_bounds = f.variables['lon_bounds'][:]

    #get the initial date from the filename
    year = fileList[i][24:28]
    month = fileList[i][28:30]
    day = fileList[i][30:32]
    
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
    df['lat'] = np.nan
    df['lon'] = np.nan
    
    #unmask the bounds - 3D data
    unmasked_lat = lat_bounds.filled(np.nan)
    unmasked_lon = lon_bounds.filled(np.nan)
    
    #get the median along each set
    lat_median = np.median(unmasked_lat, axis=0)
    lon_median = np.median(unmasked_lon, axis=0) 
    
    #now get the medians along each row
    lat_median = np.median(lat_median, axis=1)
    lon_median = np.median(lon_median, axis=1) 
    
    #get an array of the bounds for each (0 = 3D axis)
    max_lat_bound = np.max(unmasked_lat, axis=0)
    min_lat_bound = np.min(unmasked_lat, axis=0)
    max_lon_bound = np.max(unmasked_lon, axis=0)
    min_lon_bound = np.min(unmasked_lon, axis=0)
    
    #get the min & max across each row to make plotting simpler
    max_lat = np.nanmin(max_lat_bound, axis=1)
    min_lat = np.nanmin(min_lat_bound, axis=1)
    max_lon = np.nanmin(max_lon_bound, axis=1)
    min_lon = np.nanmin(min_lon_bound, axis=1)

    #------------------------------------------------------------
    #use dummy bounds to get all the data at once
    #near LA - 1km = 1/111 deg lat, so +-200 on either side
    #near LA - 1km = 1/85 deg lon, so +-100 on either side
    
    new_min_lat_bound = min_lat_bound - 250
    new_max_lat_bound = max_lat_bound + 250
    
    new_min_lon_bound = min_lon_bound - 200
    new_max_lon_bound = max_lon_bound + 200
    
    #also get a dummy lat/lon starting point - use LA city center
    la_lat = 34.051056
    la_lon = -118.251667
        
    #Check for matching latitudes within the bounds
    match_lat = np.where((la_lat >= new_min_lat_bound) & (la_lat <= new_max_lat_bound))[0]
    #Check for matching longitudes within the buffer
    match_lon = np.where((la_lon >= new_min_lon_bound) & (la_lon <= new_max_lon_bound))[0]
    #Find the intersection of matching latitudes and longitudes
    match_indices = np.intersect1d(match_lat, match_lon)
    
    if match_indices.size != 0:
        #Get row and column indices
        rows, columns = np.unravel_index(match_indices, new_min_lat_bound.shape)
        
        #Now add in the matching HCHO data for each pod
        for k in range(len(rows)):
            df.loc[my_datetime[k], 'HCHO'] = hcho[rows[k],columns[k]]
    
    #close out of this file
    f.close()

    # %% lat/lon map (colored by HCHO concentration)
    
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
    sc = ax4.scatter(max_lon, max_lat, c=df['HCHO'], cmap='viridis', s=3, transform=plate,label='GCAS Tracks')

    # Add a colorbar
    cbar = fig4.colorbar(sc, ax=ax4, orientation='vertical', pad=0.05, shrink=0.7)
    cbar.set_label('HCHO (molec/cm2)')
    
    # Define normalization
    norm = mcolors.Normalize(vmin=df['HCHO'].min(), vmax=df['HCHO'].max())  # Normalize based on data
    
    #next add the pod data so it sits on top
    #has to match the current date, then loop through each location
    for k in range(len(locations)):
       #get the right pod
       if locations[k] == 'Redlands':
           hcho_list = Redlands_HCHO
           alt_list = Redlands_alt
       elif locations[k] == 'Whittier':
           hcho_list = Whittier_HCHO
           alt_list = Whittier_alt
       elif locations[k] == 'TMF':
           hcho_list = TMF_HCHO    
           alt_list = TMF_alt
        
       for l in range(len(dates)):
           #check if the date matches our pod data
           if dates[l] == '{}-{}-{}'.format(year,month,day):
               #make sure we have HCHO data on that day
               if hcho_list[l] != 'NaN':
                    
                   #get the temperature data to convert
                   tempfilename = '{}_temp.csv'.format(pods[k])
                   #get the full file path & read it in
                   podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\RB STAQS Field 2024'
                   tempfilepath = os.path.join(podPath, tempfilename)
                   temp = pd.read_csv(tempfilepath,index_col=0) 
                   #remove any negatives
                   temp = temp[temp.iloc[:, 0] >= 0]
                   #Rename the index to match that of the pandora
                   temp = temp.rename_axis('datetime')
                   #Convert the index to a DatetimeIndex and set the nanosecond values to zero
                   temp.index = pd.to_datetime(temp.index)
                   #retime to get daily measurements
                   temp = temp.resample('D').median()
                   #Change the temperature column name
                   temp.columns.values[0] = 'temperature'
                    
                   #get the median temperature for this day
                   daily_temp = temp.loc[dates[l]][0]
                    
                   #convert the ppb value to molec/cm2
                   pod_hcho = (1/hcho_list[l])*(alt_list[l])*(1/daily_temp)*(1/0.08206)*(10**-10)*(6.022*(10**-23))
                   #get the necessary color   
                   ax4.scatter(longitudes[k], latitudes[k],c=sc.cmap(norm(hcho_list[l])), edgecolor='black', s=40, transform=plate, label='{}'.format(locations[k]))
    
    #get rid of nans in our min/max
    max_lon = max_lon[~np.isnan(max_lon)]
    max_lat = max_lat[~np.isnan(max_lat)]
    
    #Calculate the buffer values
    x_buffer = .1 * (max(max_lon) - min(max_lon))
    y_buffer = .1 * (max(max_lat) - min(max_lat))

    #Adjust the extent based on the buffer
    ax4.set_extent([min(max_lon) - x_buffer, max(max_lon) + x_buffer, min(max_lat) - y_buffer, max(max_lat) + y_buffer], crs=ccrs.PlateCarree())
    
    fig4.tight_layout()
    
    #Adding a title to fig4
    fig4.suptitle('GCAS HCHO - {}/{}/{}'.format(year,month,day), y=0.95)  # Adjust the vertical position (0 to 1)
    
    #add a legend
    #ax4.legend(loc='upper right')

    #Display the plot
    plt.show()
    
    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\GCAS HCHO Outputs\\'
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'GCAS_HCHO_map_{}_{}_{}'.format(year,month,day))
    # Save the figure to a filepath
    fig4.savefig(savePath)