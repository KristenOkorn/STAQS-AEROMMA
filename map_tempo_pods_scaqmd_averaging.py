# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 14:30:10 2024

@author: okorn
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 09:10:36 2024

Pull in TEMPO backdrop based on this training: https://gaftp.epa.gov/Air/aqmg/bhenders/presentations/pyrsig/pyrsig_geoxo_2024-05_training.pdf

Then layer pods & SQADMD sites

L3 needs debugging

This is averages from all of August, Sept, Oct, & overall - but no GCAS

@author: okorn

ADD ADDITIONAL LOCATIONS!! DOESNT JUST HAVE TO BE ONES WITH GCAS OVERLAP
"""
# Import Libraries
import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
import netCDF4 as nc

from pyproj import Proj, transform
import xarray as xr
import pyrsig
import pycno
import getpass
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

#select level of tempo data to use
level = 'L3'

#user selected date range
daterange = 'Average Aug-Oct'

#----Get set up for the ground data----

#need to pluck out just the lat/lon pairs that are relevant to each pod location
podlocations = ['TMF','Whittier','Redlands','AFRC','Caltech']
podlatitudes = [34.38189,33.97676,34.05985,34.95991,34.13685]
podlongitudes = [-117.67809,-118.03032,-117.14573,-117.88107,-118.12608]
pods = ['YPODA2','YPODA7','YPODL5','YPODR9','YPODG5']

#split into pods vs scaqmd
slocations = ['St Anthony','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park']#'AFRC','Caltech',
slatitudes = [33.9185,33.89011,33.87049,33.83718,33.82494,33.81917,33.80229,33.78136,33.78199,33.78607]#34.95991,34.13685,
slongitudes = [-118.40796,-118.4016,-118.3129,-118.33148,-118.26844,-118.21152,-118.22021,-118.21363,-118.26758,-118.2864]#-117.88107,-118.12608,

#----------------------------------------------
#Now load in the tempo data for this date range
    
#Choose domain for TEMPO data
if level == 'L2':
    locname = 'LAbasin'
elif level == 'L3':
    locname = 'LAbasinL3'
bbox = (-119, 33.4, -116.4, 34.7)

#get the dates to loop through for each
if daterange == 'August':
    # Generate a list of all dates in the month
    dates = pd.date_range(start='2023-08-02', end='2023-08-31', freq='D')
elif daterange == 'September':
    dates = pd.date_range(start='2023-09-01', end='2023-09-30', freq='D')
elif daterange == 'October':
    dates = pd.date_range(start='2023-10-01', end='2023-10-31', freq='D')    
elif daterange == 'Average Aug-Oct':
    dates = pd.date_range(start='2023-08-01', end='2023-10-31', freq='D')     
 
#Initialize a list to hold daily datasets
datasets = []

#Loop through each date and fetch the data
for date in dates:
    #Format the date as required by the API
    bdate = date.strftime('%Y-%m-%d') 
    
    #get the api to pull this data
    api = pyrsig.RsigApi(bdate=bdate, bbox=bbox, workdir=locname, gridfit=True)
    # api_key = getpass.getpass('Enter TEMPO key (anonymous if unknown):')
    api_key = 'anonymous'  # using public, so using anonymous
    api.tempo_kw['api_key'] = api_key
    
    #If you need to clear the cache, navigate to the folder and delete the old files
    #ex: C:\Users\okorn\Documents\2023 STAQS\LAbasin if workdir = LAbasin

    #Look through the descriptions for the key we need
    descdf = api.descriptions()
    
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
    
    #also need sub key
    tempoikey = 'VERTICAL_COLUMN' 

    try:
        #Use pyrsig to pull this data (KO took out xr to fix error)
        daily_df = api.to_dataframe(tempokey)
        
        #Also get the data as an xarray Dataset
        #daily_ds = xr.Dataset.from_dataframe(daily_df)
   
        #Append the dataset to the list
        #datasets.append(daily_ds)
        
        #V2 data pull - gridded for map
        api.grid_kw
        # Now retrieve a NetCDF file with IOAPI coordinates (like CMAQ)
        daily_ds = api.to_ioapi(tempokey)
      
        #Append the dataset to the list
        datasets.append(daily_ds)
        
        #make sure we're pulling the vertical column
        tempoikey = 'VERTICAL_COLUMN' 

    except pd.errors.EmptyDataError:
        #skip this file if its empty
        print(f"No data or empty file for {bdate}. Skipping.")
        continue
    
    except Exception as e:
        #skip this file if its corrupt
        print(f"Error processing data for {bdate}: {e}")
        continue
        
#Combine the daily datasets along the time dimension ('TSTEP')
ds_combined = xr.concat(datasets, dim='TSTEP')

#Replace negative values with NaN
ds_combined[tempoikey] = ds_combined[tempoikey].where(ds_combined[tempoikey] >= 0, 0)

#Compute the average over this time step
monthly_mean = ds_combined.mean(dim='TSTEP')

#need to copy over the mapping elements to monthly_mean
if 'crs_proj4' in ds_combined.attrs:
    monthly_mean.attrs['crs_proj4'] = ds_combined.attrs['crs_proj4']

#leave in molec/cm2 - convert over the rest
    
#----------------------------------------------
#Plot the TEMPO data as the background

#Get the projection ready for a map
cno = pycno.cno(monthly_mean.crs_proj4)
#Plot the data
qm = monthly_mean[tempoikey].where(lambda x: x > 0).mean(('LAY')).plot(
cbar_kwargs={'label': 'HCHO (molec/cm2)'})
#draw in the map features - coastlines
cno.drawstates(resnum=1)
    
#----------------------------------------------
#Just added this to try to get common color scheme for all subplots
#Not finished adding yet
# Get global min/max values for consistent color scaling
vmin = monthly_mean[tempoikey].where(lambda x: x > 0).min().item()
vmax = monthly_mean[tempoikey].where(lambda x: x > 0).max().item()
#----------------------------------------------

#Get the current axes
ax = plt.gca()
#Extract the colormap and normalization from the map plot
cmap = qm.get_cmap()  
norm = qm.norm        

# Convert lat/lon to map coordinates if necessary
# Example: If qm is in a projected coordinate system
proj_qm = Proj(ds_combined.crs_proj4)  # Projection of the qm map
lon_lat_proj = Proj(proj='latlong')  # Latitude/Longitude

#----------------------------------------------

#Now add the pod data - HCHO

for n in range(len(pods)):

    podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\RB STAQS Field 2024'
    #get the filename for the pod
    podfilename = "{}_HCHO.csv".format(pods[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    podfilepath = os.path.join(podPath, podfilename)
    pod = pd.read_csv(podfilepath,index_col=0)  
    #remove any negatives
    pod = pod[pod.iloc[:, 0] >= 0]
    #Rename the index to match that of the pandora
    pod = pod.rename_axis('datetime')
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    pod.index = pd.to_datetime(pod.index,format="%d-%b-%Y %H:%M:%S",errors='coerce')
    #Change the pollutant column name
    pod.columns.values[0] = 'INSTEP HCHO'
    #If redlands, need to subtract out the hours still?
    
    #now limit to between 7am - 7pm (when tempo collects)
    #but in utc, this is 2pm - 2am (crosses midnight)
    pod = pod[(pod.index.hour >= 14) | (pod.index.hour < 2)]
    #now limit the data to just our desired dates
    pod=pod[pod.index.normalize().isin(dates)]
    
    #now load in the temperature data to do the conversion
    
    #get the temperature data to convert
    tempfilename = '{}_temp_2023.csv'.format(pods[n])
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
    #retime to get hourly measurements
    temp = temp.resample('H').median()
    #Change the temperature column name
    temp.columns.values[0] = 'temperature'
                            
    #merge with the pod data
    podmerge = pd.merge(pod,temp,left_index=True, right_index=True)
                            
    #convert the ppb value to molec/cm2 - assuming all HCHO is below 1000m
    pod_hcho = podmerge['INSTEP HCHO'] * (1/podmerge['temperature']) * 2000 * (6.022/0.0821) * (10**13)
    
    #get the overall average for this time period
    pod_avg = pod_hcho.mean()
               
    #transform the lat/lon before plotting
    pod_x, pod_y = transform(lon_lat_proj, proj_qm, podlongitudes[n], podlatitudes[n])
                   
    #get the necessary color and scatter 
    
    #always scatter for non-Redlands sites
    if not podmerge.empty:
        ax.scatter(pod_x, pod_y,c=cmap(norm(pod_avg)), marker = 's', edgecolor='white', s=40)
 
#----------------------------------------------
#Now add the scaqmd data - HCHO   

for k in range(len(slocations)):

    scaqmdPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\SCAQMD Data\\'
    #get the filename for the pod
    scaqmdfilename = "{}.csv".format(slocations[k])
    #read in the first worksheet from the workbook myexcel.xlsx
    scaqmdfilepath = os.path.join(scaqmdPath, scaqmdfilename)
    scaqmd = pd.read_csv(scaqmdfilepath,index_col=0)
    #make sure the ppb values are interpreted as numbers
    scaqmd.iloc[:, 0] = scaqmd.iloc[:, 0].replace('--', np.nan).astype(float)
    #remove any negatives
    scaqmd = scaqmd[scaqmd.iloc[:, 0] >= 0]
    #Rename the index to match that of the pandora
    scaqmd = scaqmd.rename_axis('datetime')
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    scaqmd.index = pd.to_datetime(scaqmd.index,format="%m/%d/%Y %H:%M:%S %p",errors='coerce')
    #now limit to between 7am - 7pm (when tempo collects)
    #this is 2pm - 2am UTC
    scaqmd = scaqmd[(scaqmd.index.hour >= 14) | (scaqmd.index.hour < 2)]
    #convert from pst to utc
    scaqmd.index += pd.to_timedelta(7, unit='h')
    #re-average to daily
    scaqmd = scaqmd['HCHO'].resample('D').mean()
    #now limit the data to just our desired dates
    scaqmd = scaqmd[scaqmd.index.normalize().isin(dates)]
    
    #now load in the temperature data - need to pull from WU
    scaqmdtempPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\SCAQMD Data\\'
    #get the filename for the pod
    if slocations[k] == 'St Anthony' or slocations[k] == 'Manhattan Beach' or slocations[k] == 'Guenser Park' or slocations[k] =='Elm Avenue':
        scaqmdtempfilename = "temp_hawthorne.csv"
    else:
        scaqmdtempfilename = "temp_longbeach.csv"
    #read in the first worksheet from the workbook myexcel.xlsx
    scaqmdtempfilepath = os.path.join(scaqmdtempPath, scaqmdtempfilename)
    stemp = pd.read_csv(scaqmdtempfilepath,index_col=0) 
    #remove any negatives
    stemp = stemp[stemp.iloc[:, 0] >= 0]
    #convert from F to K
    stemp['temp_K'] = ((5/9)*stemp['avg temp (f)']) + 459.67
    #Rename the index to match that of the pandora
    stemp = stemp.rename_axis('datetime')
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    stemp.index = pd.to_datetime(stemp.index,errors='coerce')
    #now limit the data to just our desired dates
    stemp = stemp[stemp.index.isin(pd.to_datetime(dates))]
    
    #merge our SCAQMD datasets
    scaqmd_merge = pd.merge(scaqmd,stemp,left_index=True, right_index=True)
                         
    #convert the ppb value to molec/cm2
    scaqmd_hcho = scaqmd_merge['HCHO'] * (1/scaqmd_merge['temp_K']) * 2000 *(6.022/0.0821) * (10**13)
    
    #replace infinities with nan
    scaqmd_hcho = scaqmd_hcho.replace([np.inf, -np.inf], np.nan)
    
    #now get the overall average of converted values
    scaqmd_avg = scaqmd_hcho.median()
         
    #transform the lat/lon before plotting
    scaqmd_x, scaqmd_y = transform(lon_lat_proj, proj_qm, slongitudes[k], slatitudes[k])
  
    #get the necessary color and scatter 
    if not scaqmd_merge.empty:
        ax.scatter(scaqmd_x, scaqmd_y,c=cmap(norm(scaqmd_avg)), edgecolor='white', s=40)

#----------------------------------------------
#Final beautification

#Customize axis labels
plt.xlabel('')  # Set x-axis label
plt.ylabel('')   # Set y-axis label
plt.title('LA Basin HCHO {}'.format(daterange))   # Set plot title

#Remove x and y ticks
plt.xticks([])  # Removes x-axis ticks
plt.yticks([])  # Removes y-axis ticks

#Adjust the aspect ratio to 1:1 to avoid distortion
#plt.gca().set_aspect('equal', adjustable='box')
#Rescale lat-lon to match 
#min_xlim, min_ylim = transform(lon_lat_proj, proj_qm, -120, 32)
#max_xlim, max_ylim = transform(lon_lat_proj, proj_qm, -115, 35)
#Manually adjust x-y limits
#plt.xlim([min_xlim, max_xlim])  # Set correct longitude limits
#plt.ylim([min_ylim,max_ylim])  # Set correct latitude limits

#Show plot
plt.show()
    
#Access the figure object
fig = qm.axes.get_figure()
#save to a different folder so we don't confuse the script on the next iteration
Spath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\TEMPO HCHO Outputs\\'
#Create the full path with the figure name
savePath = os.path.join(Spath,'TEMPO_L3_avg_HCHO_map_{}_2000m'.format(daterange))
#Save the figure to a filepath
fig.savefig(savePath)
