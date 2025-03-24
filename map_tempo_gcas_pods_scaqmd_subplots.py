# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 09:10:36 2024

Pull in TEMPO backdrop based on this training: https://gaftp.epa.gov/Air/aqmg/bhenders/presentations/pyrsig/pyrsig_geoxo_2024-05_training.pdf

Then layer pods & SQADMD sites

Makes subplots for each day

Update 3/20/25 - I should add code here to get the actual correct range of pod values during the overpass and average them
Same thing with the pod temperature (in local not UTC except L5)

Also add TEMPO column to all altitude plots
@author: okorn
"""
# Import Libraries
import pandas as pd
import os
import numpy as np
from datetime import timedelta
import netCDF4 as nc

from pyproj import Proj, transform
import pyrsig
import pycno
import matplotlib.pyplot as plt

#select level of tempo data to use
level = 'L3'

#----Get set up for the ground data----

#need to pluck out just the lat/lon pairs that are relevant to each pod location
locations = ['TMF','Whittier','Redlands','AFRC','Caltech','St Anthony','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park']
latitudes = [34.95991,34.38189,34.13685,33.97676,34.05985,33.9185,33.89011,33.87049,33.83718,33.82494,33.81917,33.80229,33.78136,33.78199,33.78607]
longitudes = [-117.88107,-117.67809,-118.12608,-118.03032,-117.14573,-118.40796,-118.4016,-118.3129,-118.33148,-118.26844,-118.21152,-118.22021,-118.21363,-118.26758,-118.2864]

#dates where we have data overlapping with GCAS
dates = ['2023-08-22','2023-08-23','2023-08-25','2023-08-26']

#Create empty min/max to hold the values of the TEMPO data
global_vmin = []
global_vmax = []

#Initialize subplots
fig, axes = plt.subplots(1, len(dates), figsize=(20, 5), sharex=True, sharey=True)

#get the matching ground data for plotting later
matchPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\GCAS HCHO Outputs'
matchfileName = 'GCAS_pod_match.csv'
matchfilepath = os.path.join(matchPath, matchfileName)
match = pd.read_csv(matchfilepath,index_col=0) 

#------------------------------------------------------------
#Load in the TEMPO data to get the min/max over all dates
for date in dates:
    
    #Choose domain for TEMPO data
    if level == 'L2':
        locname = 'LAbasin'
    elif level == 'L3':
        locname = 'LAbasinL3'
    bbox = (-119, 33.4, -116.4, 34.7)
    #bbox = (-118.6, 33.8, -117, 34.2)
    bdate = date
    
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
    #descdf = api.descriptions()
    
    if level == 'L2':
        #pull out the one we want 
            tempokey = 'tempo.l2.hcho.vertical_column'
            #other ones that might be useful
            #tempo.l2.no2.vertical_column_troposphere
            #tempo.l2.hcho.fitted_slant_column
            #tempo.l2.o3tot.column_amount_o3
    elif level == 'L3':
        tempokey = 'tempo.l3.hcho.vertical_column'
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
    #----------------------------------------------

    #Convert lat/lon to map coordinates
    proj_qm = Proj(ds.crs_proj4)  # Projection of the qm map
    lon_lat_proj = Proj(proj='latlong')  # Latitude/Longitude

    #Subset the dataset for the specified time range
    ds_filtered = ds.sel(TSTEP=slice('{} 15:00'.format(date), '{} 15:30'.format(date)))
    
    #Calculate min and max for this date's tempo data
    date_min = ds_filtered[tempoikey].where(lambda x: x > 0).mean(('TSTEP', 'LAY')).min().values
    date_max = ds_filtered[tempoikey].where(lambda x: x > 0).mean(('TSTEP', 'LAY')).max().values
    
    #Update global min/max
    global_vmin.append(date_min)
    global_vmax.append(date_max)
        
#once all dates are counted, get the overall min & max
o_vmin = min(global_vmin)
o_vmax = min(global_vmax)

#----------------------------------------------
#Now prep to plot the TEMPO data as the background

#(need to load it in again now that we have the min/max)

for j, date in enumerate(dates):
    #can keep all parameters from before, just need to reload the date
    #re-pull using api
    api = pyrsig.RsigApi(bdate=date, bbox=bbox, workdir=locname, gridfit=True)
    #redo api key just in case
    api.tempo_kw['api_key'] = api_key
    #Use pyrsig to pull this data (KO took out xr to fix error)
    dff = api.to_dataframe(tempokey)
    #V2 data pull - gridded for map (ds)
    api.grid_kw
    # Now retrieve a NetCDF file with IOAPI coordinates (like CMAQ)
    ds = api.to_ioapi(tempokey)
    
    #----------------------------------------------
    #Now we're actually ready to plot tempo
    
    # Select the correct subplot
    ax = axes[j]  

    #Subset dataset for the current date
    ds_filtered = ds.sel(TSTEP=slice(f"{date} 15:00", f"{date} 15:30"))
    
    #Get the projection ready for a map
    cno = pycno.cno(ds_filtered.crs_proj4)
        
    #Plot the data
    qm = ds_filtered[tempoikey].where(lambda x: x > 0).mean(('TSTEP', 'LAY')).plot(
        ax = ax,
        vmin = o_vmin,
        vmax = o_vmax,
        add_colorbar = False)

    # Add title for each subplot
    ax.set_title(str(date))
        
    #draw in the map features - coastlines
    cno.drawstates(resnum=1)
    
    #----------------------------------------------
    #Now load the GCAS data
    
    #get the date string without dashes
    clean_date = date.replace("-", "")
    #get the filename
    filename = 'staqs-GCAS-HCHO_LaRC-G3_{}_R0.nc'.format(clean_date)
    #get the filepath
    path = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\GCAS HCHO\\'
    #Create full file path for reading file
    filePath = os.path.join(path, filename)

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

    #convert seconds past midnight to HH:MM:SS
    hours, remainder = divmod(time, 3600)
    minutes, seconds = divmod(remainder, 60)
    seconds = np.round(seconds) #round seconds the nearest whole number

    #Convert to datetime array
    my_datetime = []
    for h, m, s in zip(hours.flat, minutes.flat, seconds.flat):
        delta = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
        my_datetime.append(str(date) + str(delta))    
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
    
    #Extract the colormap and normalization from the map plot
    #cmap = qm.get_cmap()  
    #norm = qm.norm        
    
    #Get GCAS on the same color scale as TEMPO
    max_x, max_y = transform(lon_lat_proj, proj_qm, max_lon, max_lat)
           
    #Now add the GCAS data - lat/lon minimums first
    sc = ax.scatter(max_x, max_y, c=df['HCHO'], cmap=qm.get_cmap(), norm=qm.norm, s=20)
    #edgecolor='black', linewidth=0.5,
        
    #----------------------------------------------
    #Now add the ground data - both pods & scaqmd
    for k in range(len(locations)):
       
        #transform the lat/lon before plotting
        pod_x, pod_y = transform(lon_lat_proj, proj_qm, longitudes[k], latitudes[k])
        
        #get the necessary color and scatter  
        ax.scatter(pod_x, pod_y,c=match.loc[match.index[k], date], cmap=qm.get_cmap(), norm=qm.norm, marker = 's',edgecolor='white', s=40)
        
        #Remove x&y axis labels
        ax.set_xlabel('')
        ax.set_ylabel('')
#----------------------------------------------
#Final beautification

# Remove x and y ticks
plt.xticks([])  # Removes x-axis ticks
plt.yticks([])  # Removes y-axis ticks

#Add a single vertical colorbar based on qm
fig.subplots_adjust(right=0.85)  # Adjust space for colorbar
cbar_ax = fig.add_axes([0.88, 0.15, 0.02, 0.7])  # Position for vertical colorbar
fig.colorbar(qm, cax=cbar_ax, label='HCHO (molec/cm²)')  # Use the last `qm` for colorbar

# Set overall title
fig.suptitle("LA Basin HCHO", fontsize=16)

#Adjust layout and show plot
plt.tight_layout(rect=[0, 0, 0.88, 1])  # Leave space for colorbar
plt.show()

# Access the figure object
fig = qm.axes.get_figure()
#save to a different folder so we don't confuse the script on the next iteration
Spath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\TEMPO HCHO Outputs\\'
#Create the full path with the figure name
savePath = os.path.join(Spath,'TEMPO_L3_GCAS_HCHO_map_{}_2000m_subplots'.format(date))
# Save the figure to a filepath
fig.savefig(savePath)
