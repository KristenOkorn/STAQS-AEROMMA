# -*- coding: utf-8 -*-
"""
Created on Thu May 23 20:02:23 2024

Altitude plot of HALO CH4 data + INSTEP

Also add TCCON


@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import math

#get the relevant location data for each
locations = ['Whittier','Redlands','Caltech','TMF'] #'AFRC'
pods = ['YPODA7','YPODL5','YPODG5','YPODA2'] #'YPODR9'

#pollutant?
pollutant = 'CH4'

for n in range(len(locations)): 
    #-------------------------------------
    #load in the HALO data
    haloPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\HALO XCH4\\'
    #get the filename for the pod
    halofilename = "HALO_XCH4_{}.csv".format(locations[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    halofilepath = os.path.join(haloPath, halofilename)
    halo = pd.read_csv(halofilepath,index_col=0)  
    #remove any negatives
    halo = halo[halo.iloc[:, 0] >= 0]
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    halo.index = pd.to_datetime(halo.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
    
    #-------------------------------------
    #now load in the matching pod data - CH4
    podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\RB STAQS Field 2024'
    #get the filename for the pod
    podfilename = "{}_CH4.csv".format(pods[n])
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
    pod.columns.values[0] = 'INSTEP CH4'
    #add a column for altitude - will all be 0
    pod['INSTEP altitude'] = 0
    
    #get the data into UTC (from PDT) #different for each pod!!
    if locations[n] != 'Redlands':
        pod.index += pd.to_timedelta(7, unit='h')
    
    #-------------------------------------
    
    #now load in the matching TCCON data - Caltech & AFRC only
    if locations[n] == 'Caltech' or locations[n] == 'AFRC':
       tcconPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\TCCON'
       #get the filename for the tccon data
       tcconfilename = "{}_TCCON.csv".format(locations[n])
       #read in the first worksheet from the workbook myexcel.xlsx
       tcconfilepath = os.path.join(tcconPath, tcconfilename)
       tccon = pd.read_csv(tcconfilepath,index_col=0)  
       #Convert the index to a DatetimeIndex and set the nanosecond values to zero
       tccon.index = pd.to_datetime(tccon.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
       #resample to minutely
       tccon = tccon.resample('T').median()
       #Change the pollutant column name
       tccon.rename(columns={'CH4':'TCCON CH4', 'CO2':'TCCON CO2'}, inplace=True)
    
    #-------------------------------------
       
    #no merge needed here - revisit if this turns out to not be true
    
    #-------------------------------------

    #Get global min/max to standardize x & y axes
    x_max = math.ceil(max(halo['XCH4'].max(), pod['INSTEP CH4'].max()))
    x_min = math.ceil(min(halo['XCH4'].min(), pod['INSTEP CH4'].min())) -0.22
    y_max = halo['altitude'].max() +80
    y_min = -80
    
    #-------------------------------------
    
    #figure out how many days we have - for how many subplots
    num_unique_days = len(np.unique(halo.index.date))
    #also get the list of them to split by
    unique_days_list = np.unique(halo.index.date).tolist()
    
    # Create a dictionary to store DataFrames for each unique day
    split_dataframes = {}

    #Split the DataFrame based on unique days
    for day in unique_days_list:
        day_data = halo[halo.index.date == day]
        split_dataframes[day] = day_data
    
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(num_unique_days, 1, figsize=(8, 4 * num_unique_days))
    
    # If there is only one subplot, make it a list to handle indexing
    if num_unique_days == 1:
        axs = [axs]

    for k, (day, df) in enumerate(split_dataframes.items()):
        #make a set of y's for the lidar data
        df['HALO_alt'] = np.linspace(0, max(df['altitude']), len(df))
    
        #first plot the flight data
        axs[k].scatter(df['XCH4'], df['HALO_alt'], label='HALO', color='orange')
        
        #then plot the instep data
        pod_filtered = pod[(pod.index >= df.index.min()) & (pod.index <= df.index.max())]
        axs[k].scatter(pod_filtered['INSTEP CH4'], pod_filtered['INSTEP altitude'], label='INSTEP', color='red')
        
        #then plot the tccon data if applicable
        if locations[n] == 'Caltech' or locations[n] == 'AFRC':
            #filter to just the times of overlap with HALO
            tccon_filtered = tccon[(tccon.index >= df.index.min()) & (tccon.index <= df.index.max())]
            #get the altitude for ch4
            tccon_filtered['altitude'] = np.linspace(0, y_max, len(tccon_filtered))
            #now median
            tccon_filtered['TCCON CH4'] = np.nanmedian(tccon_filtered['TCCON CH4'])
            #and create a linspace of only 15 points so its not too crowded on the plot
            lin_ch4 = tccon_filtered.iloc[np.linspace(0, len(tccon_filtered) - 1, 15, dtype=int)]['TCCON CH4']
            lin_alt = tccon_filtered.iloc[np.linspace(0, len(tccon_filtered) - 1, 15, dtype=int)]['altitude']
            axs[k].scatter(lin_ch4, lin_alt, label='TCCON', color='purple')

        #-------------------------------------

        #Add a title with the date to each subplot
        axs[k].set_title('{}'.format(day), y=.9)  # Adjust the vertical position (0 to 1)
        axs[k].legend(loc='upper right', bbox_to_anchor=(1.0, 0.9))
        
        #Set the font size of the tick labels
        axs[k].tick_params(axis='both', labelsize=12)
        
        #Standardize the axes
        axs[k].set_xlim(x_min, x_max)
        axs[k].set_ylim(y_min, y_max)
        axs[k].autoscale(False)
        
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.2, top=0.9, bottom=0.15)  # You can adjust the value as needed
    #Single y-axis label for all subplots
    fig.text(0.03, 0.5, 'Altitude (m)', va='center', rotation='vertical',fontsize=16)
    #Common x-axis label for all subplots
    #fig.text(0.5, 0.1, 'HCHO (ppb)', ha='center',fontsize=16)
    axs[-1].set_xlabel('CH4 (ppm)', ha='center',fontsize=16)
    #Add an overall title to the plot
    fig.text(0.5,0.91,'{}'.format(locations[n]), ha = 'center', fontsize=16, weight = 'bold')

    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\HALO Plots\\'
    
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'altitude_HALO_CH4_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)
