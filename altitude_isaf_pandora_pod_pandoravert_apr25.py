
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
import math

#get the relevant location data for each
locations = ['Whittier','Caltech','Redlands'] #'TMF', 'AFRC'
pods = ['YPODA7','YPODG5','YPODL5'] #'YPODA2', 'YPODR9
#locations = ['St Anthony','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park'] #'AFRC'
#pods = ['St Anthony','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park'] #'YPODR9'

for n in range(len(locations)): 
    
    #-------------------------------------
    #load in the in-situ data - ISAF HCHO
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
    #-------------------------------------
    if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
        #now load in the pandora data
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
        #-------------------------------------
        #now load in the surface pandora data
    
        #get the filename for pandora
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
 
    #-------------------------------------
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
    #add a column for altitude - will all be 0
    pod['INSTEP altitude'] = 0
    
    #need to get in UTC time to match the DC-8 & Pandora
    #L5 & L9 already good, convert the rest
    if pods[n] != 'YPODL5' or pods[n] != 'YPODL9':
        pod.index = pod.index + timedelta(hours = 7)
    #-------------------------------------
    #'as of' merge - just to match up the time windows, not the exact times
    merges = pd.merge_asof(isaf, pod, left_index=True, right_index=True, tolerance=pd.Timedelta('1H'),  direction='nearest')           
    #-------------------------------------
    
    if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
        #filter to match times for pandora also - get the start and end times from the merge file
        start_time = isaf.index[0]
        end_time = isaf.index[-1]
        #now filter pandora based on this
        pandora = pandora[(pandora.index >= start_time) & (pandora.index <= end_time)]
        pandora2 = pandora2[(pandora2.index >= start_time) & (pandora2.index <= end_time)]
        surfpandora = surfpandora[(surfpandora.index >= start_time) & (surfpandora.index <= end_time)]
        
        #remove missing values for ease of plotting
        pandora = pandora.dropna()
        pandora2 = pandora2.dropna()
        surfpandora = surfpandora.dropna()
        
        #Create a dictionary to store DataFrames for each unique day
        pandora_split_dataframes = {}
        pandora2_split_dataframes = {}
        surfpandora_split_dataframes = {}
        
    
    #-------------------------------------
    
    #Create a dictionary to store DataFrames for each unique day
    split_dataframes = {}
    p2_split_dataframes = {}
    surf_split_dataframes = {}
    
    #-------------------------------------    
    #Get global min/max to standardize x & y axes
    x_max = math.ceil(max(merges[' CH2O_ISAF'].max(), merges['INSTEP HCHO'].max()))
    y_max = math.ceil(merges['altitude'].max() +80)
    
    #and use 0 for all mins - 80s are so points don't get cut off at the edges
    x_min = 0
    y_min = -80
    
    #overwrite y_max if whittier - one high point messing up the scale
    if locations[n] == 'Whittier':
        y_max = math.ceil(isaf.loc[isaf['altitude'] < 5000, 'altitude'].max() + 80)
        
    #-------------------------------------
    #figure out how many days we have - for how many subplots
    num_unique_days = len(np.unique(isaf.index.date))
    #also get the list of them to split by
    unique_days_list = np.unique(isaf.index.date).tolist()
    
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(num_unique_days, 1, figsize=(8, 4 * num_unique_days))
    
    # If there is only one subplot, make it a list to handle indexing
    if num_unique_days == 1:
        axs = [axs]
    
    #-------------------------------------
    
    #Split the DataFrame based on unique days
    for day in unique_days_list:
        day_data = isaf[isaf.index.date == day]
        split_dataframes[day] = day_data
    
        if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
            #now repeat for the pandora profile data
            pandora_day_data = pandora[pandora.index.date == day]
            pandora_split_dataframes[day] = pandora_day_data
            #and the regular pandora data
            p2_day_data = pandora2[pandora2.index.date == day]
            p2_split_dataframes[day] = p2_day_data
            #and the pandora surface data
            surf_day_data = surfpandora[surfpandora.index.date == day]
            surf_split_dataframes[day] = surf_day_data
    
    #-------------------------------------
    
    #create columns as needed for pandora data
    for k, (day, df) in enumerate(p2_split_dataframes.items()):
        if locations[n] == 'Whittier' or locations[n] == 'TMF' or locations[n] == 'AFRC':
            # Get daily data for Pandora and surface
            p2_day_data = p2_split_dataframes.get(day)
            surf_day_data = surf_split_dataframes.get(day)
            
            #create a regular set of y's (altitude) for the Pandora tropo data
            df['altitude'] = np.linspace(0, y_max, len(df))
            #now median
            df['Pandora Tropo HCHO'] = np.nanmedian(df['Pandora Tropo HCHO'])
            #and create a linspace of only 15 points so its not too crowded on the plot
            lin_hcho = df.iloc[np.linspace(0, len(df) - 1, 15, dtype=int)]['Pandora Tropo HCHO']
            lin_alt = df.iloc[np.linspace(0, len(df) - 1, 15, dtype=int)]['altitude']
            #now plot the pandora tropo data
            axs[k].scatter(lin_hcho, lin_alt, label='Pandora Tropo HCHO', color='blue')
            
            #also add a set of y's at 0 for the surface pandora estimatea
            surf_day_data['Pandora_alt'] = np.linspace(0, 0, len(surf_day_data))
            #plot the surface data in the same loop to avoid looping issues
            axs[k].scatter(surf_day_data['Pandora Surface HCHO'], surf_day_data['Surface Pandora altitude'], label='Pandora Surface Estimate', color='green')
        
    #-------------------------------------
    
    #vertical pandora data for pandora locations only
    if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
        #handle the pandora vertical profile data separately
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
               axs[k].scatter(x, y, label='Pandora Profile', color='cyan')
           else: #plot normally
               #get the HCHO values from the evens/ odds
               x = vdf.iloc[0,1::2]  # Odd-indexed columns: 1, 3, 5, ...
               #separate out just the heights
               y_temp = vdf.iloc[0, 0::2]  # columns 0, 2, 4, ...
               #get the average height to use
               y = (y_temp.shift(-1) + y_temp) / 2
               y = y[:-1]  # Drop the last NaN created by the shift
               #and plot
               axs[k].scatter(x, y, label='Pandora Profile', color='cyan')
        
    
        #Add a title with the date to each subplot
        axs[k].set_title('{}'.format(day), y=.9)  # Adjust the vertical position (0 to 1)
     
        #then plot the flight data
        for k, (day, df) in enumerate(split_dataframes.items()):
            axs[k].scatter(df[' CH2O_ISAF'], df['altitude'], label='ISAF', color='black')
        
            #then plot the instep data
            pod_filtered = pod[(pod.index >= df.index.min()) & (pod.index <= df.index.max())]
            axs[k].scatter(pod_filtered['INSTEP HCHO'], pod_filtered['INSTEP altitude'], label='INSTEP', color='red')
            
            #Set the font size of the tick labels
            axs[k].tick_params(axis='both', labelsize=12)
            #Standardize the axes
            axs[k].set_xlim(x_min, x_max)
            axs[k].set_ylim(y_min, y_max)
            axs[k].autoscale(False)
            
            #Now plot the legend
            axs[k].legend(loc='upper right', bbox_to_anchor=(1.0, 0.7)) 
        
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
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\ISAF HCHO Plots\\'
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'altitude_HCHO_vert_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)
