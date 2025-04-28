# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 08:20:02 2025

3D wind data for the DC-8 / INSTEP coincidences
for when ISAF & pod HCHO are aligned
also try a 3d quiver plot to show the same info

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

#get the relevant location data for each
locations = ['Whittier','Caltech','Redlands','AFRC','St Anthonys','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park'] 

for n in range(len(locations)): 
    #-------------------------------------
    #load in the merge file
    isafPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\ISAF Outputs\\'
    #get the filename for the pod
    isaffilename = "ISAF_HCHO_{}.csv".format(locations[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    isaffilepath = os.path.join(isafPath, isaffilename)
    isaf = pd.read_csv(isaffilepath,index_col=0)  
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    isaf.index = pd.to_datetime(isaf.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
    #-------------------------------------
    #this data is already filtered for when its near each location - leave it at that
    #(no need to merge)
    #-------------------------------------
    
    #figure out how many days we have - for how many subplots
    num_unique_days = len(np.unique(isaf.index.date))
    #also get the list of them to split by
    unique_days_list = np.unique(isaf.index.date).tolist()
    
    # Create a dictionary to store DataFrames for each unique day
    split_dataframes = {}

    #Split the DataFrame based on unique days
    for day in unique_days_list:
        day_data = isaf[isaf.index.date == day]
        split_dataframes[day] = day_data
    
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(num_unique_days, 1, figsize=(4, 4 * num_unique_days),subplot_kw={'projection':'polar'})
    
    # If there is only one subplot, make it a list to handle indexing
    if num_unique_days == 1:
        axs = [axs]

    for k, (day, df) in enumerate(split_dataframes.items()):
        #extract daily components from vectors
        speed = np.sqrt(df[' U']**2 + df[' V']**2)
        direction = np.arctan2(df[' V'], df[' U'])  
        w_color = df[' W']  # Assuming 'w' is the vertical wind component
        
        #normalize color scaling for w values over full dataset
        norm = plt.Normalize(vmin=isaf[' W'].min(), vmax=isaf[' W'].max()) 
    
        #try converting to degrees for troubleshooting
        direction_degrees = np.degrees(direction)
        #now get between 0 and 360
        direction_degrees = (direction_degrees + 360) % 360
        #now convert degrees back to radians
        direction_radians = np.radians(direction_degrees) 
    
        #scatter this day's data
        sc = axs[k].scatter(direction_radians, speed, c=w_color, norm=norm)
     
        #add a colorbar for the vertical component
        cbar = plt.colorbar(sc, ax=axs[k],pad=0.1)
        cbar.set_label('Vertical Wind Speed (m/s)')
 
        #Add a title with the date to each subplot
        axs[k].set_title('{}'.format(day), y=1.1)  # Adjust the vertical position (0 to 1)
       
        # Set the font size of the tick labels
        axs[k].tick_params(axis='both', labelsize=12)
        
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.4, top=0.9, bottom=0.05)  # You can adjust the value as needed
    #Add an overall title
    fig.suptitle('Daily Wind Roses - {}'.format(locations[n]), fontweight='bold')
    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\MMS Outputs\\'
    
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'WindRose_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)