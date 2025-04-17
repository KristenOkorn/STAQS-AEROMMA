# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 09:26:20 2025

@author: kokorn
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 09:28:40 2025
Altitude plot of DC-8, Pandora, & pod
Updated Pandora conversion info
For Pandora: use filter for same window instead of merge for exact alignment
Also leave out the limiting one (filter should work for this too)

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from datetime import timedelta

#get the relevant location data for each
locations = ['TMF','Whittier','AFRC'] #'Caltech','Redlands',
pods = ['YPODA2','YPODA7','YPODR9'] #'YPODG5','YPODL5',
#locations = ['St Anthony','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park'] #'AFRC'
#pods = ['St Anthony','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park'] #'YPODR9'

#pollutant?
pollutant = 'HCHO'

for n in range(len(locations)): 
    
    #-------------------------------------
    #load in the in-situ data - ISAF HCHO
    isafPath = 'C:\\Users\\kokorn\\Documents\\AGES+\\ISAF'
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
    #-------------------------------------
   
    #now load in the pandora data
    pandoraPath = 'C:\\Users\\kokorn\\Documents\\AGES+\\Pandora\\'
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
    
    #-------------------------------------
    podPath = 'C:\\Users\\kokorn\\Documents\\AGES+\\Pods\\'
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
    #add a column for altitude - will all be 0
    pod['INSTEP altitude'] = 0
    
    #need to get in UTC time to match the DC-8 & Pandora
    #L5 & L9 already good, convert the rest
    if pods[n] != 'YPODL5' or pods[n] != 'YPODL9':
        pod.index = pod.index + timedelta(hours = 7)
    #-------------------------------------
   
    #merge our dataframes
    merge = pd.merge(isaf,pod,left_index=True, right_index=True)

    #filter to match times for pandora also - get the start and end times from the merge file
    start_time = merge.index[0]
    end_time = merge.index[-1]
    #now filter based on this
    pandora = pandora[(pandora.index >= start_time) & (pandora.index <= end_time)]
    
    #-------------------------------------
    
    #remove missing values for ease of plotting
    merge = merge.dropna()
    pandora = pandora.dropna()
    
    #-------------------------------------
    #figure out how many days we have - for how many subplots
    num_unique_days = len(np.unique(merge.index.date))
    #also get the list of them to split by
    unique_days_list = np.unique(merge.index.date).tolist()
    
    # Create a dictionary to store DataFrames for each unique day
    split_dataframes = {}
    pandora_split_dataframes = {}

    #Split the DataFrame based on unique days
    for day in unique_days_list:
        day_data = merge[merge.index.date == day]
        split_dataframes[day] = day_data
        #now repeat for the pandora data
        pandora_day_data = pandora[pandora.index.date == day]
        pandora_split_dataframes[day] = pandora_day_data

            
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(num_unique_days, 1, figsize=(8, 4 * num_unique_days))
    
    # If there is only one subplot, make it a list to handle indexing
    if num_unique_days == 1:
        axs = [axs]

    for k, (day, df) in enumerate(split_dataframes.items()):
       #first plot the pandora data - need to reformat for vertical profiles
       if len(pandora_day_data) >1: #have to average if more than 1 profile
           column_averages = pandora_day_data.mean() #take the mean
           #get the HCHO values from the evens/ odds
           x = column_averages.iloc[1::2].reset_index(drop=True)
           #separate out just the heights
           y_temp = column_averages.iloc[0::2]  # columns 0, 2, 4, ...
           #get the average height to use
           y = (y_temp.shift(-1) + y_temp) / 2
           y = y[:-1]  # Drop the last NaN created by the shift
           #and plot
           axs[k].scatter(x, y, label='Pandora Profile', color='purple')
       else: #plot normally
           #get the HCHO values from the evens/ odds
           x = pandora_day_data.iloc[0,1::2]  # Odd-indexed columns: 1, 3, 5, ...
           #separate out just the heights
           y_temp = pandora_day_data.iloc[0, 0::2]  # columns 0, 2, 4, ...
           #get the average height to use
           y = (y_temp.shift(-1) + y_temp) / 2
           y = y[:-1]  # Drop the last NaN created by the shift
           #and plot
           axs[k].scatter(x, y, label='Pandora Profile', color='purple')
            
       #then plot the flight data
       axs[k].scatter(df[' CH2O_ISAF'], df['altitude'], label='ISAF', color='black')
       #then plot the instep data
       axs[k].scatter(df['INSTEP HCHO'], df['INSTEP altitude'], label='INSTEP', color='red')
        
       #Add a title with the date to each subplot
       axs[k].set_title('{}'.format(day), y=.9)  # Adjust the vertical position (0 to 1)
       axs[k].legend(loc='upper right', bbox_to_anchor=(1.0, 0.9))
        
       #Set the font size of the tick labels
       axs[k].tick_params(axis='both', labelsize=12)
        
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.2, top=0.9, bottom=0.05)  # You can adjust the value as needed
    #Single y-axis label for all subplots
    fig.text(0.03, 0.5, 'Altitude (m)', va='center', rotation='vertical',fontsize=16)
    #Common x-axis label for all subplots
    #fig.text(0.5, 0.1, 'HCHO (ppb)', ha='center',fontsize=16)
    axs[-1].set_xlabel('HCHO (ppb)', ha='center',fontsize=16)
    #Add an overall title to the plot
    fig.text(0.5,0.91,'{}'.format(locations[n]), ha = 'center', fontsize=16, weight = 'bold')

    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\kokorn\\Documents\\AGES+\\Plots\\'
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'altitude_HCHO_vert_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)