# -*- coding: utf-8 -*-
"""
Created on Thu May 23 21:07:52 2024


Altitude plot of Picarro CH4 data + INSTEP

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

#pollutant?
pollutant = 'CH4'

for n in range(len(locations)): 
    #-------------------------------------
    #load in the PICARRO data
    picarroPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\Picarro CO2 CH4 CO\\'
    #get the filename for the pod
    picarrofilename = "Picarro_CH4_CO2_{}.csv".format(locations[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    picarrofilepath = os.path.join(picarroPath, picarrofilename)
    picarro = pd.read_csv(picarrofilepath,index_col=0)  
    #remove any negatives
    picarro = picarro[picarro.iloc[:, 0] >= 0]
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    picarro.index = pd.to_datetime(picarro.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
   
    #convert altitude - file is off by a factor of 10
    picarro['altitude'] = picarro['altitude']/10
    
    #Convert ppb to ppm
    picarro['CH4_ppb'] = picarro['CH4_ppb']/1000
    #remove any negatives (again)
    picarro = picarro[picarro['CH4_ppb'] >= 0]
    
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
    #merge our dataframes
    merge = pd.merge(picarro,pod,left_index=True, right_index=True)
    
    #remove missing values for ease of plotting
    merge = merge.dropna()
    
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
    fig, axs = plt.subplots(num_unique_days, 1, figsize=(8, 4 * num_unique_days))
    
    # If there is only one subplot, make it a list to handle indexing
    if num_unique_days == 1:
        axs = [axs]

    for k, (day, df) in enumerate(split_dataframes.items()):
        
        #create a regular set of y's (altitude) for the Pandora tropo data
        df['Pandora_alt'] = np.linspace(0, max(df['altitude']), len(df))
    
        #first plot the flight data
        axs[k].scatter(df['CH4_ppb'], df['altitude'], label='Picarro', color='black')
        #then plot the instep data
        axs[k].scatter(df['INSTEP CH4'], df['INSTEP altitude'], label='INSTEP', color='red')
        #Add a title with the date to each subplot
        axs[k].set_title('{}'.format(day), y=.9)  # Adjust the vertical position (0 to 1)
        axs[k].legend(loc='upper right', bbox_to_anchor=(1.0, 0.9))
        
        # Set the font size of the tick labels
        axs[k].tick_params(axis='both', labelsize=12)
        
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.2, top=0.9, bottom=0.05)  # You can adjust the value as needed
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
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\Picarro Plots\\'
    
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'altitude_CH4_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)