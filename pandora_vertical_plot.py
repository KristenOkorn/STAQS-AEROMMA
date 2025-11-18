# -*- coding: utf-8 -*-
"""
Created on Mon Nov 10 15:22:43 2025

Plot vertical pandora data to understand typical vertical profiles

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import math

#get pandora locations only
locations = ['Whittier','AFRC','TMF']
pods = ['YPODA7','YPODR9','YPODA2']
colors = ["salmon", "skyblue", "lightgreen"]

for n in range(len(locations)): 
    
    #load in the pandora vertical data
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
    
    #limit to just study dates
    pandora = pandora.loc['8-1-2023':'10-31-2023']
    
    #-------------------------------------
    
    #figure out how many days we have - for how many subplots
    num_unique_days = len(np.unique(pandora.index.date))
    #also get the list of them to split by
    unique_days_list = np.unique(pandora.index.date).tolist()
    
    cols = math.ceil(math.sqrt(num_unique_days))
    rows = math.ceil(num_unique_days/ cols)
    
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(rows, cols, figsize=(cols * 4, rows * 3))
    axs = axs.flatten()
    
    # If there is only one subplot, make it a list to handle indexing
    if num_unique_days == 1:
        axs = [axs]
    
    #-------------------------------------
    #Create a dictionary to store DataFrames for each unique day
    pandora_split_dataframes = {}
    
    #Split the DataFrame based on unique days
    for day in unique_days_list:
        pandora_day_data = pandora[pandora.index.date == day]
        pandora_split_dataframes[day] = pandora_day_data
          
    #-------------------------------------    
    #Get global min/max to standardize x & y axes
    #x_max = math.ceil(max(merges[' CH2O_ISAF'].max(), merges['INSTEP HCHO'].max()))
    #y_max = math.ceil(merges['altitude'].max() +80)
    
    #and use 0 for all mins - 80s are so points don't get cut off at the edges
    #x_min = 0
    #y_min = -80
    
    #-------------------------------------
    
    #plot the vertical pandora data
    for k, (vday, vdf) in enumerate(pandora_split_dataframes.items()):
           #first plot the pandora data - need to reformat for vertical profiles
           if len(vdf) <1:
               pass #skip plotting if there's no profile during this spiral
           elif len(vdf) >1: #have to average if more than 1 profile
               column_averages = vdf.mean() #take the mean
               #get the HCHO values from the evens/ odds
               x = column_averages.iloc[1::2].reset_index(drop=True)
               #separate out just the heights
               y_temp = column_averages.iloc[0::2]  # columns 0, 2, 4, ...
               #get the average height to use
               y = (y_temp.shift(-1) + y_temp) / 2
               y = y[:-1]  # Drop the last NaN created by the shift
               #and plot
               #axs[k].scatter(x, y, label='Pandora Profile', color='cyan')
               axs[k].plot(x, y, marker='o', linestyle='-')
               
           else: #plot normally
               #get the HCHO values from the evens/ odds
               x = vdf.iloc[0,1::2]  # Odd-indexed columns: 1, 3, 5, ...
               #separate out just the heights
               y_temp = vdf.iloc[0, 0::2]  # columns 0, 2, 4, ...
               #get the average height to use
               y = (y_temp.shift(-1) + y_temp) / 2
               y = y[:-1]  # Drop the last NaN created by the shift
               #and plot
               #axs[k].scatter(x, y, label='Pandora Profile', color='cyan')
               axs[k].plot(x, y, marker='o', linestyle='-')
               
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
    savePath = os.path.join(Spath,'altitude_Pandora_vert_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)
