# -*- coding: utf-8 -*-
"""
Created on Wed Feb  5 12:05:40 2025

3D wind data for the DC-8 / INSTEP coincidences
for when Picarro & pod CH4 are aligned
also try a 3d quiver plot to show the same info

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from datetime import datetime
from matplotlib.lines import Line2D

#get the relevant location data for each
locations = ['TMF','Whittier','Redlands','AFRC'] #'AFRC'
pods = ['YPODA2','YPODA7','YPODL5','YPODR9'] #'YPODR9'

for n in range(len(locations)): 
    #-------------------------------------
    #load in the merge file
    picarroPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\Picarro CO2 CH4 CO\\'
    #get the filename for the pod
    picarrofilename = "Picarro_CH4_CO2_{}.csv".format(locations[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    picarrofilepath = os.path.join(picarroPath, picarrofilename)
    picarro = pd.read_csv(picarrofilepath,index_col=0)  
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    picarro.index = pd.to_datetime(picarro.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
    #-------------------------------------
    
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
    
    #get the data into UTC (from PDT) #different for each pod!!
    if locations[n] != 'Redlands':
        pod.index += pd.to_timedelta(7, unit='h')
    
    #-------------------------------------
    #merge our dataframes
    merge = pd.merge(picarro,pod,left_index=True, right_index=True)
    
    #remove missing values for ease of plotting
    merge = merge.dropna()
    
    #-------------------------------------
    
    #compute wind speed & angle from our u&v vectors
    speed = np.sqrt(merge[' U']**2 + merge[' V']**2)
    direction = np.arctan2(merge[' V'], merge[' U']) #angle
    #convert radians to degrees (for polar plot)
    direction = np.degrees(direction)
    #convert to 0-360 range
    direction[direction < 0] += 360
    
    #-------------------------------------
    #normalize the vertical direction for color mapping
    norm = plt.Normalize(merge[' W'].min(),merge[' W'].max())
    w_color = plt.cm.viridis(norm(merge[' W']))
    #-------------------------------------
    #figure out how many days we have - for how many subplots
    num_unique_days = len(np.unique(merge.index.date))
    #also get the list of them to split by
    unique_days_list = np.unique(merge.index.date).tolist()
    
    # Create a dictionary to store DataFrames for each unique day
    split_dataframes = {}

    #Split the DataFrame based on unique days
    for day in unique_days_list:
        day_data = merge[merge.index.date == day]
        split_dataframes[day] = day_data
    
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(num_unique_days, 1, figsize=(4, 4 * num_unique_days),subplot_kw={'projection':'polar'})
    
    # If there is only one subplot, make it a list to handle indexing
    if num_unique_days == 1:
        axs = [axs]

    for k, (day, df) in enumerate(split_dataframes.items()):
        #edit below here for desired plot!!
        sc = axs[k].scatter(np.radians(direction), speed, c=w_color,norm=norm)
        
        #add a colorbar for the vertical component
        cbar = plt.colorbar(sc, ax=axs[k])
        cbar.set_label('Vertical Wind Speed (m/s)')
        tick_values = np.linspace(merge[' W'].min(),merge[' W'].max(),num=5)
        normalized_tick_values = norm(tick_values)
        cbar.set_ticks(normalized_tick_values)
        cbar.set_ticklabels([f"{int(round(tick))}" for tick in tick_values])
        
        #Add a title with the date to each subplot
        axs[k].set_title('{}'.format(day), y=1.1)  # Adjust the vertical position (0 to 1)
       
        # Set the font size of the tick labels
        axs[k].tick_params(axis='both', labelsize=12)
        
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.4, top=0.9, bottom=0.05)  # You can adjust the value as needed
    #Single y-axis label for all subplots
    #fig.text(0.03, 0.5, 'Altitude (m)', va='center', rotation='vertical',fontsize=16)
    #Common x-axis label for all subplots
    #fig.text(0.5, 0.1, 'HCHO (ppb)', ha='center',fontsize=16)
    #axs[-1].set_xlabel('CH4 (ppm)', ha='center',fontsize=16)
    #Add an overall title to the plot
    fig.text(0.5,0.92,'Daily Wind Roses - {}'.format(locations[n]), ha = 'center', fontsize=16, weight = 'bold')

    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\MMS Outputs\\'
    
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'WindRose_CH4_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)