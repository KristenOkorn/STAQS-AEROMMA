# -*- coding: utf-8 -*-
"""
Created on Fri Jan 30 13:34:37 2026

Ozone altitude plot updated for 2026

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from datetime import datetime
import math
from datetime import datetime, timedelta

#get the relevant location data for each
locations = ['Redlands','Whittier','AFRC']
pods = ['YPODL5','YPODA7','YPODR9']

#pollutant?
pollutant = 'O3'

#define threshold for gaps in data to be counted as separate flights
#most flights are about 5hrs long
gap_threshold = pd.Timedelta(hours=2)

for n in range(len(locations)): 
    #-------------------------------------
    #load in the DC-8 in-situ data - CL O3
    clPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\CL O3 Outputs\\'
    #get the filename for the pod
    clfilename = "CL_O3_{}.csv".format(locations[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    clfilepath = os.path.join(clPath, clfilename)
    cl = pd.read_csv(clfilepath,index_col=0)  
    #remove any negatives
    cl = cl[cl.iloc[:, 0] >= 0]
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    cl.index = pd.to_datetime(cl.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
    #convert altitude - file is off by a factor of 10
    cl['altitude'] = cl['altitude']/10
    #re-average to minute to match pod
    cl = cl.resample('1T').mean()
    #remove missing - need to define different coincidences
    cl = cl.dropna()
    
    #time difference between consecutive rows
    dt = cl.index.to_series().diff()
    #new flight whenever the threshold gap is exceeded (not midnight bc crossover UTC issues)
    new_coin = (dt.isna()) | (dt >= gap_threshold)
    #flight counter (global)
    coin_id = new_coin.cumsum() -1
    #add to the isaf df
    cl["coincidence"] = coin_id.astype(int)
    #get the start & end and pad +/- 1hr on each side 
    pad = pd.Timedelta(hours=1)
    #make sure the count is numeric
    cl["coincidence"] = pd.to_numeric(cl["coincidence"])
    #now create coincidence window with pad (-1 to zero index)
    coin_windows = {coin : (grp.index.min() - pad, grp.index.max() + pad) for coin, grp in cl.groupby("coincidence")}
    
    #Set up min/maxes for later
    cl_max = max(cl['O3_CL'])
    alt_max = max((cl['altitude']) + 80)
    #and use 0 for all mins - 80s are so points don't get cut off at the edges
    x_min = 0
    y_min = -80
    
    #-------------------------------------
    #next load in the pandora column csv's - skip for non-pandora locations
    if locations[n] != 'Redlands' and locations[n] != 'Caltech':
        pandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
        #get the filename for pandora
        pandorafilename = "{}_column_extra_O3.csv".format(locations[n])
        #join the path and filename
        pandorafilepath = os.path.join(pandoraPath, pandorafilename)
        pandora = pd.read_csv(pandorafilepath,index_col=1)
        #Reset the seconds to zero in the index
        pandora.index = pandora.index.str.replace(r'\d{2}$', '00')
        #Convert the index to a DatetimeIndex
        pandora.index = pd.to_datetime(pandora.index)#rename index to datetime
        pandora = pandora.rename_axis('datetime')
        #resample to minutely - since pod data will be minutely
        pandora = pandora.resample('T').mean()
        #remove any negatives
        pandora = pandora[pandora.iloc[:, 0] >= 0]
        #Filter so the lowest quality flag is omitted
        pandora = pandora.loc[pandora['quality_flag'] != 12]
        
        #need to pull in temperature from a different file - just use WU
        tempPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\O3\\Temperatures'
       
        #get the filename for the pod
        if locations[n] == 'AFRC':
            tempfilename = "MojaveT.xlsx"
        else:
            tempfilename = "SouthCoastT.xlsx"
            
        #read in the first worksheet from the workbook myexcel.xlsx
        tempfilepath = os.path.join(tempPath, tempfilename)
        temp = pd.read_excel(tempfilepath,index_col=0) 
        #remove any negatives
        temp = temp[temp.iloc[:, 0] >= 0]
        #convert from F to K
        temp['temp_K'] = ((5/9)*temp.iloc[:,0]) + 459.67
        #Rename the index to match that of the pandora
        temp = temp.rename_axis('datetime')
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        temp.index = pd.to_datetime(temp.index,errors='coerce')
        #since this is hourly, need to downsample to minutely
        temp = temp.resample("T").ffill() 
        
        #merge the pandora temperature with the pandora data (as of merge to find nearest rather than exact match)
        pmerge = pd.merge_asof(pandora, temp, left_index=True, right_index=True, tolerance=pd.Timedelta('1H'),  direction='nearest')  
        #convert from mol/m2 to ppb - use 50km as top of stratosphere
        pmerge['Pandora Column O3'] = pmerge['O3']*0.08206*pmerge['temp_K']*(10**6)/(50000)
        
        
        #now group the pandora data by coincidence
        pmerge["coincidence"] = pd.NA
        #add in the grouping windows
        for coin, (t0, t1) in coin_windows.items(): 
            mask = (pmerge.index >= t0) & (pmerge.index <= t1) 
            pmerge.loc[mask, "coincidence"] = coin
        #drop rows that didn't match any window
        pmerge = pmerge.dropna(subset=["coincidence"])

    #-------------------------------------
    #now load in the matching pod data - O3
    podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\R1 STAQS Field'
    #get the filename for the pod
    podfilename = "{}_O3_field_corrected.csv".format(pods[n])
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
    pod.columns.values[0] = 'INSTEP O3'
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
    pod_max = max(pod['INSTEP O3'])
    #and now get the overall max
    if cl_max > pod_max:
        global_max = cl_max
    else:
        global_max = pod_max
    
    
    #-------------------------------------
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
        cl_lim = cl[cl["coincidence"] == coin]
        pod_lim = pod[pod["coincidence"] == coin]
        
        #first plot the flight data
        if not cl_lim.empty:
            ax.scatter(cl_lim['O3_CL'], cl_lim['altitude'], label='Chemiluminescence', color='black')
        #then plot the instep data
        if not pod_lim.empty:
            ax.scatter(pod_lim['INSTEP O3'], pod_lim['INSTEP altitude'], label='INSTEP', color='magenta')

        #Pandora data next (Pandora locations only)
        if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
            pandora_lim = pmerge[pmerge["coincidence"] == coin]
            #now pandora data
            if not pandora_lim.empty:
                #create a regular set of y's (altitude) for the Pandora tropo data
                pandora_lim['altitude'] = np.linspace(0, alt_max, len(pandora_lim))
                #now median
                pandora_lim['Pandora Column O3'] = np.nanmedian(pandora_lim['Pandora Column O3'])
                #and create a linspace of only 15 points so its not too crowded on the plot
                lin_o3 = pandora_lim.iloc[np.linspace(0, len(pandora_lim) - 1, 15, dtype=int)]['Pandora Column O3']
                lin_alt = pandora_lim.iloc[np.linspace(0, len(pandora_lim) - 1, 15, dtype=int)]['altitude']
                #now plot the pandora tropo data
                ax.scatter(lin_o3, lin_alt, label='Pandora O3', color='blue')
                
        
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
        ax.set_xlabel('O3 (ppb)')
        ax.set_ylabel('Altitude (m)')
            
        #-------------------------------------
        
    
    #-----Finishing touches for the overall figure-----    
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.2, top=0.9, bottom=0.05)  # You can adjust the value as needed
    #Single y-axis label for all subplots
    #fig.text(0.03, 0.5, 'Altitude (m)', va='center', rotation='vertical',fontsize=16)
    #Common x-axis label for all subplots
    #fig.text(0.5, 0.1, 'HCHO (ppb)', ha='center',fontsize=16)
    #axs[-1].set_xlabel('O3 (ppb)', ha='center',fontsize=16)
    #Add an overall title to the plot
    fig.text(0.5,0.91,'{}'.format(locations[n]), ha = 'center', fontsize=16, weight = 'bold')
    
    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\O3 Plots\\'
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'altitude_O3_{}newcoincidences_2hr'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)