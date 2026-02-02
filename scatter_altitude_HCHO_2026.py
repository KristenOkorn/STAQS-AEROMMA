# -*- coding: utf-8 -*-
"""
Created on Thu Jan 29 15:12:56 2026

Altitude plot of DC-8, Pandora, & pod

Updated to split by flight instead of by day

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from datetime import timedelta
import math
from datetime import datetime, timedelta

#get the relevant location data for each
locations = ['Whittier','Caltech','AFRC']
pods = ['YPODA7','YPODG5','YPODR9']
#locations = ['St Anthony','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park'] #'AFRC'
#pods = ['St Anthony','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park'] #'YPODR9'

#define threshold for gaps in data to be counted as separate flights
#most flights are about 5hrs long
gap_threshold = pd.Timedelta(hours=2)

for n in range(len(locations)): 
    
    #-------------------------------------
    #load in the in-situ 54756data - ISAF HCHO
    isafPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\ISAF Outputs\\'
    #get the filename for the pod
    isaffilename = "ISAF_HCHO_{}.csv".format(locations[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    isaffilepath = os.path.join(isafPath, isaffilename)
    isaf = pd.read_csv(isaffilepath,index_col=0)  
    #remove any negatives
    isaf = isaf[isaf.iloc[:, 0] >= 0]
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    isaf.index = pd.to_datetime(isaf.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
    #convert ppt to ppb
    isaf[' CH2O_ISAF'] = isaf[' CH2O_ISAF']/1000
    #convert altitude - file is off by a factor of 10
    isaf['altitude'] = isaf['altitude']/10
    #make sure these are in the correct order for splitting by flight later
    isaf = isaf.sort_index()
    
    #time difference between consecutive rows
    dt = isaf.index.to_series().diff()
    #new flight whenever the threshold gap is exceeded (not midnight bc crossover UTC issues)
    new_coin = (dt.isna()) | (dt >= gap_threshold)
    #flight counter (global)
    coin_id = new_coin.cumsum() -1
    #add to the isaf df
    isaf["coincidence"] = coin_id.astype(int)
    #get the start & end and pad +/- 1hr on each side 
    pad = pd.Timedelta(hours=1)
    #make sure the count is numeric
    isaf["coincidence"] = pd.to_numeric(isaf["coincidence"])
    #now create coincidence window with pad (-1 to zero index)
    coin_windows = {coin : (grp.index.min() - pad, grp.index.max() + pad) for coin, grp in isaf.groupby("coincidence")}
    
    #Set up min/maxes for later
    isaf_max = max(isaf[' CH2O_ISAF'])
    alt_max = max((isaf['altitude']) + 80)
    #and use 0 for all mins - 80s are so points don't get cut off at the edges
    x_min = 0
    y_min = -80
    
    #-------------------------------------
    if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
        #now load in the pandora vertical data
        pandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
        #get the filename for pandora
        pandorafilename = "{}_tropo_extra_HCHO.csv".format(locations[n])
        #join the path and filename
        pandorafilepath = os.path.join(pandoraPath, pandorafilename)
        pandora = pd.read_csv(pandorafilepath,index_col=1)
        #Reset the seconds to zero in the index
        pandora.index = pandora.index.str.replace(r'\d{2}$', '00')
        #Convert the index to a DatetimeIndex
        pandora.index = pd.to_datetime(pandora.index)#rename index to datetime
        pandora = pandora.rename_axis('datetime')
        #Filter so the lowest quality flag is omitted
        pandora = pandora.loc[pandora['quality_flag'] != 12]
        #get rid of times that don't have the vertical profile
        pandora = pandora.dropna()
        #drop unnessecarry columns - we need temp and the vertical profiles
        pandora = pandora.drop(pandora.columns[[0, 1, 2, 3, 5, 6, 7, 8]], axis=1)
        #put temperature in its own dataframe for cleaner handling
        ptemp = pd.DataFrame(pandora.pop('temperature'))
        #add a layer zero column
        pandora.insert(0, 'layer0', 0)
        #drop the top layer - i don't know how to handle the edge case
        pandora = pandora.iloc[:, :-1]
        
        #-----
        #Convert the layer heights
        for i in range(1, pandora.shape[1], 2):  # loop through odd columns
            if i - 1 >= 0 and i + 1 < pandora.shape[1]:
                left = pandora.iloc[:, i - 1]
                right = pandora.iloc[:, i + 1]
                multiplier = right - left
                #apply the full mol/m2 to ppb correction
                pandora.iloc[:, i] = pandora.iloc[:, i] * 0.08206 * ptemp['temperature'] / multiplier #taking out 1000 bc km vs m
        
        #convert km to m
        pandora.iloc[::2, :] = pandora.iloc[::2, :] * 1000
        
        #now group the pandora data by coincidence
        pandora["coincidence"] = pd.NA
        #add in the grouping windows
        for coin, (t0, t1) in coin_windows.items(): 
            mask = (pandora.index >= t0) & (pandora.index <= t1) 
            pandora.loc[mask, "coincidence"] = coin
        #drop rows that didn't match any window
        pandora = pandora.dropna(subset=["coincidence"])
       
        #-------------------------------------
        #next load in the pandora tropo csv's - skip for sites without one
        pandora2 = pd.read_csv(pandorafilepath,index_col=1)
        #Reset the seconds to zero in the index
        pandora2.index = pandora2.index.str.replace(r'\d{2}$', '00')
        #Convert the index to a DatetimeIndex
        pandora2.index = pd.to_datetime(pandora2.index)#rename index to datetime
        pandora2 = pandora2.rename_axis('datetime')
        #Filter so the lowest quality flag is omitted
        pandora2 = pandora2.loc[pandora2['quality_flag'] != 12]
        #get rid of any unnecessary columns
        pandora2 = pandora2[['HCHO','temperature','top_height','max_vert_tropo']]
        #resample to minutely - since pod data will be minutely
        #pandora = pandora.resample('T').mean()
        #Change the pollutant column name
        pandora2.columns.values[0] = 'Pandora Tropo HCHO'
        #remove any negatives
        pandora2 = pandora2[pandora2.iloc[:, 0] >= 0]
        #convert from mol/m2 to ppb
        pandora2['Pandora Tropo HCHO'] = pandora2['Pandora Tropo HCHO']*0.08206*pandora2['temperature']*1000/(pandora2['max_vert_tropo'])
        #move to PDT to match other data & avoid issues crossing midnight
        #pandora2.index = pandora2.index - timedelta(hours = 7)
        
        #now group the pandora tropo data by coincidence
        pandora2["coincidence"] = pd.NA
        #add in the grouping windows
        for coin, (t0, t1) in coin_windows.items(): 
            mask = (pandora2.index >= t0) & (pandora2.index <= t1) 
            pandora2.loc[mask, "coincidence"] = coin
        #drop rows that didn't match any window
        pandora2 = pandora2.dropna(subset=["coincidence"])
        
        #-------------------------------------
        #now load in the surface pandora data
    
        #get the filename for surface pandora
        surfpandorafilename = "{}_surface_extra_HCHO.csv".format(locations[n])
        #join the path and filename
        surfpandorafilepath = os.path.join(pandoraPath, surfpandorafilename)
        surfpandora = pd.read_csv(surfpandorafilepath,index_col=1)
        #Reset the seconds to zero in the index
        surfpandora.index = surfpandora.index.str.replace(r'\d{2}$', '00')
        #Convert the index to a DatetimeIndex
        surfpandora.index = pd.to_datetime(surfpandora.index)#rename index to datetime
        surfpandora = surfpandora.rename_axis('datetime')
        #Filter to only use high quality data
        surfpandora = surfpandora.loc[surfpandora['quality_flag'] != 12]
        #hold onto the HCHO data and relevant parameters only
        surfpandora = surfpandora[['HCHO','temperature','top_height','max_vert_tropo']]
        #resample to minutely - since pod data will be minutely
        #surfpandora = surfpandora.resample('T').mean()
        #Change the pollutant column name
        surfpandora.columns.values[0] = 'Pandora Surface HCHO'
        #remove any negatives
        surfpandora = surfpandora[surfpandora.iloc[:, 0] >= 0]
        #convert mol/m3 to ppb
        surfpandora['Pandora Surface HCHO'] = surfpandora['Pandora Surface HCHO']*0.08206*surfpandora['temperature']*(10**(9))/1000
        #add a column for altitude - will all be 0
        surfpandora['Surface Pandora altitude'] = 0
        #move to PDT to match other data & avoid issues crossing midnight
        surfpandora.index = surfpandora.index - timedelta(hours = 7)
        
        #now group the pandora surface data by coincidence
        surfpandora["coincidence"] = pd.NA
        #add in the grouping windows
        for coin, (t0, t1) in coin_windows.items(): 
            mask = (surfpandora.index >= t0) & (surfpandora.index <= t1) 
            surfpandora.loc[mask, "coincidence"] = coin
        #drop rows that didn't match any window
        surfpandora = surfpandora.dropna(subset=["coincidence"])
 
    #-------------------------------------
    #now load in the pod data
    if locations[n] == 'AFRC' or locations[n] == 'Caltech' or locations[n] == 'Redlands' or locations[n] == 'TMF' or locations[n] == 'Whittier':
        podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\R1 STAQS Field'
        #get the filename for the pod
        podfilename = "{}_HCHO_field_corrected.csv".format(pods[n])
        #read in the first worksheet from the workbook myexcel.xlsx
        podfilepath = os.path.join(podPath, podfilename)
        pod = pd.read_csv(podfilepath,index_col=0)  
        #remove any negatives
        pod = pod[pod.iloc[:, 0] >= 0]
        #Rename the index to match that of the pandora
        pod = pod.rename_axis('datetime')
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        pod.index = pd.to_datetime(pod.index,errors='coerce')
        #Change the pollutant column name
        pod.columns.values[0] = 'INSTEP HCHO'
        #add a column for altitude - will all be 0
        pod['INSTEP altitude'] = 0
        
        #now group the pod data by coincidence
        pod["coincidence"] = pd.NA
        #add in the grouping windows
        for coin, (t0, t1) in coin_windows.items(): 
            mask = (pod.index >= t0) & (pod.index <= t1) 
            pod.loc[mask, "coincidence"] = coin
        #drop rows that didn't match any window
        pod = pod.dropna(subset=["coincidence"])
        
        #also get the pod max
        pod_max = max(pod['INSTEP HCHO'])
        #and now get the overall max
        if isaf_max > pod_max:
            global_max = isaf_max
        else:
            global_max = pod_max
        
    else: #SCAQMD monitors
        podPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\SCAQMD Data\\'
        #get the filename for the pod
        podfilename = "{}.csv".format(locations[n])
        #read in the first worksheet from the workbook myexcel.xlsx
        podfilepath = os.path.join(podPath, podfilename)
        pod = pd.read_csv(podfilepath,index_col=0)
        #make sure the ppb values are interpreted as numbers
        pod.iloc[:, 0] = pod.iloc[:, 0].replace('--', np.nan).astype(float)
        #remove any negatives
        pod = pod[pod.iloc[:, 0] >= 0]
        #Rename the index to match that of the pandora
        pod = pod.rename_axis('datetime')
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        pod.index = pd.to_datetime(pod.index,format="%m/%d/%Y %H:%M:%S %p",errors='coerce')
        #convert from pst to utc
        pod.index += pd.to_timedelta(7, unit='h')
        #Change the pollutant column name
        pod.columns.values[0] = 'INSTEP HCHO'
        #add a column for altitude - will all be 0
        pod['INSTEP altitude'] = 0
        #sort index for later
        pod = pod.sort_index()
        
        #now group the pod data by coincidence
        pod["coincidence"] = pd.NA
        #add in the grouping windows
        for coin, (t0, t1) in coin_windows.items(): 
            mask = (pod.index >= t0) & (pod.index <= t1) 
            pod.loc[mask, "coincidence"] = coin
        #drop rows that didn't match any window
        pod = pod.dropna(subset=["coincidence"])
    

    #-------------------------------------
    #figure out how many days we have - for how many subplots
    num_coin= len(coin_windows)
    #also get the list of them to split by
    coin_list = coin_windows.keys()
    
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(num_coin, 1, figsize=(8, 4 * num_coin))
    
    # If there is only one subplot, make it a list to handle indexing
    if num_coin == 1:
        axs = [axs]
    
    #-------------------------------------
    #now start plotting - new subplot for each coincidence
    for l, coin in enumerate(coin_list):
        ax = axs[l]
        
        #limit  each dataframe to the current coincidence
        isaf_lim = isaf[isaf["coincidence"] == coin]
        pandora_lim = pandora[pandora["coincidence"] == coin]
        pandora2_lim = pandora2[pandora2["coincidence"] == coin]
        surfpandora_lim = surfpandora[surfpandora["coincidence"] == coin]
        pod_lim = pod[pod["coincidence"] == coin]
        
        
        #first plot the flight data
        if not isaf_lim.empty:
            ax.scatter(isaf_lim[' CH2O_ISAF'], isaf_lim['altitude'], label='ISAF', color='black')
        #then plot the instep data
        if not pod_lim.empty:
            ax.scatter(pod_lim['INSTEP HCHO'], pod_lim['INSTEP altitude'], label='INSTEP', color='magenta')
        
        #Pandora data next (Pandora locations only)
        if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
            #tropospheric data first    
            if not pandora2_lim.empty:
                #create a regular set of y's (altitude) for the Pandora tropo data
                pandora2_lim['altitude'] = np.linspace(0, alt_max, len(pandora2_lim))
                #now median
                pandora2_lim['Pandora Tropo HCHO'] = np.nanmedian(pandora2_lim['Pandora Tropo HCHO'])
                #and create a linspace of only 15 points so its not too crowded on the plot
                lin_hcho = pandora2_lim.iloc[np.linspace(0, len(pandora2_lim) - 1, 15, dtype=int)]['Pandora Tropo HCHO']
                lin_alt = pandora2_lim.iloc[np.linspace(0, len(pandora2_lim) - 1, 15, dtype=int)]['altitude']
                #now plot the pandora tropo data
                ax.scatter(lin_hcho, lin_alt, label='Pandora Tropo HCHO', color='blue')
                
            #surface pandora data next
            if not surfpandora_lim.empty:
                #also add a set of y's at 0 for the surface pandora estimatea
                surfpandora_lim['Pandora_alt'] = np.linspace(0, 0, len(surfpandora_lim))
                #plot the surface data
                ax.scatter(surfpandora_lim['Pandora Surface HCHO'], surfpandora_lim['Surface Pandora altitude'], label='Pandora Surface Estimate', color='green')
                    
            #plot the vertical distribution last
            if not pandora_lim.empty:
                #first plot the pandora data - need to reformat for vertical profiles
                if len(pandora_lim) >1:
                    #need to limit to 1 profile - chose middle of window
                    idx = round(len(pandora_lim)/2)
                    #get the profile from the middle as our only
                    pandora_lim = pandora_lim.iloc[[idx]]
                    #get the HCHO values from the evens/ odds
                    x = pandora_lim.iloc[0,1::2]  # Odd-indexed columns: 1, 3, 5, ...
                    #separate out just the heights
                    y = pandora_lim.iloc[0, 0::2]  # columns 0, 2, 4, ...
                    #and plot
                    ax.scatter(x, y, label='Pandora Profile', color='cyan')
                
                
        #---Subplot Beautification---
        #Set the font size of the tick labels
        ax.tick_params(axis='both', labelsize=12)
        #Standardize the axes
        ax.set_xlim(x_min, global_max)
        ax.set_ylim(y_min, alt_max)
        ax.autoscale(False)
            
        #Now plot the legend
        ax.legend(loc='upper right', bbox_to_anchor=(1.0, 0.7)) 
            
        #Add a subtitle with the location & coincidence to each subplot
        ax.set_title('{} - Coincidence {}'.format(locations[n],l), y=.9)  # Adjust the vertical position (0 to 1)
            
        #nov25 version - individual x&y axis labels for each subplot
        ax.set_xlabel('HCHO (ppb)')
        ax.set_ylabel('Altitude (m)')
            
        #-------------------------------------
    
             
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.2, top=0.9, bottom=0.05)  # You can adjust the value as needed
    #Single y-axis label for all subplots
    #fig.text(0.03, 0.5, 'Altitude (m)', va='center', rotation='vertical',fontsize=16)
    #Common x-axis label for all subplots
    #fig.text(0.5, 0.1, 'HCHO (ppb)', ha='center',fontsize=16)
    #axs[-1].set_xlabel('HCHO (ppb)', ha='center',fontsize=16)
    #Add an overall title to the plot
    fig.text(0.5,0.91,'{}'.format(locations[n]), ha = 'center', fontsize=16, weight = 'bold')
    
    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\ISAF HCHO Plots\\'
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'altitude_HCHO_vert_{}_newcoincidences_2hr'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)