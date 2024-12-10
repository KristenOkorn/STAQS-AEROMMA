# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 09:10:36 2024

Pull in TEMPO backdrop based on this training: https://gaftp.epa.gov/Air/aqmg/bhenders/presentations/pyrsig/pyrsig_geoxo_2024-05_training.pdf

Then layer pods & SQADMD sites

L3 needs debugging

Also compare with models - HRRR is with the tempo data

Also add TEMPO column to all altitude plots
@author: okorn
"""
# Import Libraries
import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
from tkinter.filedialog import askdirectory
import netCDF4 as nc

from pyproj import Proj, transform
import xarray as xr
import pyrsig
import pycno
import getpass
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

#select level of tempo data to use
level = 'L2'

#filter for time?
timefilter = 'yes'

#Prompt user to select folder for analysis
path = askdirectory(title='Select Folder for analysis').replace("/","\\")

#Get the list of files from this directory
from os import listdir
from os.path import isfile, join
fileList = [f for f in listdir(path) if isfile(join(path, f))]

#----Get set up for the ground data----

#need to pluck out just the lat/lon pairs that are relevant to each pod location
podlocations = ['TMF','Whittier','Redlands']#'AFRC','Caltech',
podlatitudes = [34.38189,33.97676,34.05985]#34.95991,34.13685,
podlongitudes = [-117.67809,-118.03032,-117.14573]#-117.88107,-118.12608,
pods = ['YPODA2','YPODA7','YPODL5']

#split into pods vs scaqmd
slocations = ['St Anthony','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park']#'AFRC','Caltech',
slatitudes = [33.9185,33.89011,33.87049,33.83718,33.82494,33.81917,33.80229,33.78136,33.78199,33.78607]#34.95991,34.13685,
slongitudes = [-118.40796,-118.4016,-118.3129,-118.33148,-118.26844,-118.21152,-118.22021,-118.21363,-118.26758,-118.2864]#-117.88107,-118.12608,

#sites & dates where we have data overlapping with GCAS
dates = ['2023-08-22','2023-08-23','2023-08-25','2023-08-26']
Whittier_HCHO = [2.04375,2.14523,2.93427,'NaN']
Whittier_alt = [8663.8766,6726.1166,9049.99255,'NaN']
TMF_HCHO = [2.04375,2.14523,2.93427,'NaN']
TMF_alt = [8663.877,6726.1167,9049.9926,'NaN']
Redlands_HCHO = [2.04375,2.14523,2.93427,'NaN']
Redlands_alt=[8663.87657,6726.1166,9049.99255,'NaN']
StAnthony_HCHO = [2.42,0.49,3.02,0]
StAnthony_alt = [6805.2603,5657.095,9043.99505,5584.2833]
StAnthony_temp = [294.261,293.622,292.556,293.311]
ManhattanBeach_HCHO = [0,0,0,0]
ManhattanBeach_alt = [6805.2603,5657.095,9043.99505,5584.2833]
ManhattanBeach_temp = [294.261,293.622,292.556,293.311]
GuenserPark_HCHO = [0,0,2.42,2.48]
GuenserPark_alt = [6805.2603,5657.095,9043.99505,5584.2833]
GuenserPark_temp = [294.261,293.622,292.556,293.311]
ElmAve_HCHO = [0,0.04,1.64,0.46]
ElmAve_alt = [6805.2603,5657.095,9043.99505,5584.2833]
ElmAve_temp = [294.261,293.622,292.556,293.311]
Judson_HCHO = [0,0,1.29,0]
Judson_alt = [6805.2603,5657.095,9043.99505,5584.2833]
Judson_temp = [296.25,296.761,295.35,296.856]
StLuke_HCHO = [0,0,1.73,0]
StLuke_alt = [6805.2603,5657.095,9043.99505,5584.2833]
StLuke_temp = [296.25,296.761,295.35,296.856]
Hudson_HCHO = [0.27,1.98,2.41,0]
Hudson_alt = [6805.2603,5657.095,9043.99505,5584.2833]
Hudson_temp = [296.25,296.761,295.35,296.856]
InnerPort_HCHO = [1.24,2.39,1.33,0]
InnerPort_alt = [6805.2603,5657.095,9043.99505,5584.2833]
InnerPort_temp = [296.25,296.761,295.35,296.856]
FirstMethodist_HCHO = [4,0.24,1.59,3.57]
FirstMethodist_alt = [6805.2603,5657.095,9043.99505,5584.2833]
FirstMethodist_temp = [296.25,296.761,295.35,296.856]
HarborPark_HCHO = [0,0,0,0]
HarborPark_alt = [6805.2603,5657.095,9043.99505,5584.2833]
HarborPark_temp = [296.25,296.761,295.35,296.856]

#----Get set up for the GCAS data----

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

    #----------------------------------------------
    #Now load in the tempo data for this date
    
    #Choose domain for TEMPO data
    locname = 'LAbasin'
    bbox = (-119, 33.4, -116.4, 34.7)
    #bbox = (-118.6, 33.8, -117, 34.2)
    bdate = '{}-{}-{}'.format(year,month,day)

    #for my LA domain:
        #bottom left 33.7 -118.5
        #top left 34.3 -118.5
        #top right 34.3 -117.1
        #bottom right 33.7 -117.1
    
    #get the api to pull this data
    api = pyrsig.RsigApi(bdate=bdate, bbox=bbox, workdir=locname, gridfit=True)
    # api_key = getpass.getpass('Enter TEMPO key (anonymous if unknown):')
    api_key = 'anonymous'  # using public, so using anonymous
    api.tempo_kw['api_key'] = api_key
    
    #If you need to clear the cache, navigate to the folder and delete the old files
    #ex: C:\Users\okorn\Documents\2023 STAQS\LAbasin if workdir = LAbasin

    #Look through the descriptions for the key we need
    descdf = api.descriptions()
    #pull out the one we want 
    tempokey = 'tempo.l2.hcho.vertical_column'
    #other ones that might be useful
    #tempo.l2.no2.vertical_column_troposphere
    #tempo.l2.hcho.fitted_slant_column
    #tempo.l2.o3tot.column_amount_o3
    #tempo.l3.hcho.vertical_column
    #tempo.l3.o3tot.column_amount_o3

    #Use pyrsig to pull this data (KO took out xr to fix error)
    dff = api.to_dataframe(tempokey)

    #V2 data pull - gridded for map (ds)
    api.grid_kw
    # Now retrieve a NetCDF file with IOAPI coordinates (like CMAQ)
    ds = api.to_ioapi(tempokey)
    if level == 'L2':
        # Choose a column from above, notice that names are truncated, so they can be weird
        tempoikey = 'VERTICAL_COLUMN' 
    elif level == 'L3':
        tempoikey = 'VERTICAL_COLUMN' 

    #leave in molec/cm2 - convert over the rest
    
    #limit to the correct time of day (in UTC)
    if timefilter == 'yes':
        
        # Subset the dataset for the specified time range
        ds_filtered = ds.sel(TSTEP=slice('{}-{}-{} 15:00'.format(year,month,day), '{}-{}-{} 15:30'.format(year,month,day)))

        #----------------------------------------------
        #Plot the TEMPO data as the background

        #Get the projection ready for a map
        cno = pycno.cno(ds_filtered.crs_proj4)
        #Plot the data
        qm = ds_filtered[tempoikey].where(lambda x: x > 0).mean(('TSTEP', 'LAY')).plot(
        cbar_kwargs={'label': 'HCHO (molec/cm2)'})
        #draw in the map features - coastlines
        cno.drawstates(resnum=1)
        
    else:
        #----------------------------------------------
        #Plot the TEMPO data as the background

        #Get the projection ready for a map
        cno = pycno.cno(ds.crs_proj4)
        #Plot the data
        qm = ds[tempoikey].where(lambda x: x > 0).mean(('TSTEP', 'LAY')).plot(
        cbar_kwargs={'label': 'HCHO (molec/cm2)'})
        #draw in the map features - coastlines
        cno.drawstates(resnum=1)
    
    #----------------------------------------------
    #Now add the GCAS data
    
    #Get the current axes
    ax = plt.gca()
    #Extract the colormap and normalization from the map plot
    cmap = qm.get_cmap()  
    norm = qm.norm        
    
    # Convert lat/lon to map coordinates if necessary
    # Example: If qm is in a projected coordinate system
    proj_qm = Proj(ds.crs_proj4)  # Projection of the qm map
    lon_lat_proj = Proj(proj='latlong')  # Latitude/Longitude
    max_x, max_y = transform(lon_lat_proj, proj_qm, max_lon, max_lat)
    
    #Now add the GCAS data - lat/lon minimums first
    sc = ax.scatter(max_x, max_y, c=df['HCHO'], cmap=cmap, norm = norm, s=20, label='GCAS Tracks')
    #edgecolor='black', linewidth=0.5,
    
    #----------------------------------------------
    #Now add the pod data
    
    #has to match the current date, then loop through each location
    for l in range(len(dates)):
        #check if the date matches our pod data
        if dates[l] == '{}-{}-{}'.format(year,month,day):
            #get the info we need to plot the pods
            for k in range(len(podlocations)):
               #get the right pod
               if podlocations[k] == 'Redlands':
                   hcho_list = Redlands_HCHO
                   alt_list = Redlands_alt
               elif podlocations[k] == 'Whittier':
                   hcho_list = Whittier_HCHO
                   alt_list = Whittier_alt
               elif podlocations[k] == 'TMF':
                   hcho_list = TMF_HCHO    
                   alt_list = TMF_alt
               
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
                   #pod_hcho = (1/hcho_list[l])*(2000)*(1/daily_temp)*(1/0.08206)*(10**-10)*(6.022*(10**-23))
                   pod_hcho = hcho_list[l] * (1/daily_temp) * 1 * (6.022/0.0821) * (10**17)
                   
                   #transform the lat/lon before plotting
                   pod_x, pod_y = transform(lon_lat_proj, proj_qm, podlongitudes[k], podlatitudes[k])
                   
                   #get the necessary color and scatter  
                   ax.scatter(pod_x, pod_y,c=cmap(norm(hcho_list[l])), marker = 's',edgecolor='white', s=40)
                   
            for kk in range(len(slocations)):
                if slocations[kk] == 'St Anthony':
                    hcho_list = StAnthony_HCHO    
                    alt_list = StAnthony_alt
                    temp_list = StAnthony_temp
                elif slocations[kk] == 'Manhattan Beach':
                    hcho_list = ManhattanBeach_HCHO    
                    alt_list = ManhattanBeach_alt 
                    temp_list = ManhattanBeach_temp
                elif slocations[kk] == 'Guenser Park':
                    hcho_list = GuenserPark_HCHO    
                    alt_list = GuenserPark_alt 
                    temp_list = GuenserPark_temp 
                elif slocations[kk] == 'Elm Avenue':
                    hcho_list = ElmAve_HCHO    
                    alt_list = ElmAve_alt 
                    temp_list = ElmAve_temp
                elif slocations[kk] == 'Judson':
                    hcho_list = Judson_HCHO    
                    alt_list = Judson_alt   
                    temp_list = Judson_temp
                elif slocations[kk] == 'St Luke':
                    hcho_list = StLuke_HCHO    
                    alt_list = StLuke_alt  
                    temp_list = StLuke_temp 
                elif slocations[kk] == 'Hudson':
                    hcho_list = Hudson_HCHO    
                    alt_list = Hudson_alt  
                    temp_list = Hudson_temp
                elif slocations[kk] == 'InnerPort':
                    hcho_list = InnerPort_HCHO    
                    alt_list = InnerPort_alt
                    temp_list = InnerPort_temp
                elif slocations[kk] == 'FirstMethodist':
                    hcho_list = FirstMethodist_HCHO    
                    alt_list = FirstMethodist_alt    
                    temp_list = FirstMethodist_temp
                elif slocations[kk] == 'HarborPark':
                    hcho_list = HarborPark_HCHO    
                    alt_list = HarborPark_alt 
                    temp_list = HarborPark_temp
                    
                #get the average temperature for this day
                daily_temp = temp_list[l]
                         
                #convert the ppb value to molec/cm2
                if hcho_list[l] == 0: #need to add a stop if it read 0
                    scaqmd_hcho = 0
                else: #otherwise, convert normally
                    #scaqmd_hcho = (1/hcho_list[l])*(2000)*(1/daily_temp)*(1/0.08206)*(10**-10)*(6.022*(10**-23))
                    scaqmd_hcho = hcho_list[l] * (1/daily_temp) * 1 *(6.022/0.0821) * (10**17)
                    
                #transform the lat/lon before plotting
                scaqmd_x, scaqmd_y = transform(lon_lat_proj, proj_qm, slongitudes[kk], slatitudes[kk])
  
                #get the necessary color and scatter  
                ax.scatter(scaqmd_x, scaqmd_y,c=cmap(norm(hcho_list[l])), edgecolor='white', s=40)

    #----------------------------------------------
    #Final beautification

    # Customize axis labels
    plt.xlabel('')  # Set x-axis label
    plt.ylabel('')   # Set y-axis label
    plt.title('LA Basin HCHO {}-{}-{}'.format(year,month,day))   # Set plot title

    # Remove x and y ticks
    plt.xticks([])  # Removes x-axis ticks
    plt.yticks([])  # Removes y-axis ticks

    # Adjust the aspect ratio to 1:1 to avoid distortion
    #plt.gca().set_aspect('equal', adjustable='box')
    #Rescale lat-lon to match 
    #min_xlim, min_ylim = transform(lon_lat_proj, proj_qm, -120, 32)
    #max_xlim, max_ylim = transform(lon_lat_proj, proj_qm, -115, 35)
    #Manually adjust x-y limits
    #plt.xlim([min_xlim, max_xlim])  # Set correct longitude limits
    #plt.ylim([min_ylim,max_ylim])  # Set correct latitude limits
    # Show plot
    plt.show()
    
    # Access the figure object
    fig = qm.axes.get_figure()
    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\TEMPO HCHO Outputs\\'
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'TEMPO_GCAS_HCHO_map_{}_{}_{}_1m'.format(year,month,day))
    # Save the figure to a filepath
    fig.savefig(savePath)