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
locations = ['TMF','Whittier','AFRC', 'Caltech','Redlands'] 
pods = ['YPODA2','YPODA7','YPODR9', 'YPODG5','YPODL5'] 
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
    if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
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
    
    if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
        #filter to match times for pandora also - get the start and end times from the merge file
        start_time = merge.index[0]
        end_time = merge.index[-1]
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
    
    #remove missing values for ease of plotting
    merge = merge.dropna()
    
    #Create a dictionary to store DataFrames for each unique day
    split_dataframes = {}
    
    #-------------------------------------
    #figure out how many days we have - for how many subplots
    num_unique_days = len(np.unique(merge.index.date))
    #also get the list of them to split by
    unique_days_list = np.unique(merge.index.date).tolist()
    
    #Split the DataFrame based on unique days
    for day in unique_days_list:
        day_data = merge[merge.index.date == day]
        split_dataframes[day] = day_data
    
        if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
            #now repeat for the pandora profile data
            pandora_day_data = pandora[pandora.index.date == day]
            pandora_split_dataframes[day] = pandora_day_data
            #and the regular pandora data
            pandora2_day_data = pandora2[pandora2.index.date == day]
            pandora2_split_dataframes[day] = pandora2_day_data
            #and the pandora surface data
            surfpandora_day_data = surfpandora[surfpandora.index.date == day]
            surfpandora_split_dataframes[day] = surfpandora_day_data
                
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(num_unique_days, 1, figsize=(8, 4 * num_unique_days))
    
    # If there is only one subplot, make it a list to handle indexing
    if num_unique_days == 1:
        axs = [axs]
        
    #-------------------------------------    
    #Get global min/max to standardize x & y axes
    x_max = max(merge[' CH2O_ISAF'].max(), merge['INSTEP HCHO'].max()) 
    y_max = merge['altitude'].max() +80
    
    #and use 0 for all mins - 80s are so points don't get cut off at the edges
    x_min = 0
    y_min = -80
    #-------------------------------------
    
    #create columns as needed for pandora data
    for k, (day, df) in enumerate(split_dataframes.items()):
        if locations[n] == 'Whittier' or locations[n] == 'TMF' or locations[n] == 'AFRC':
            #create a regular set of y's (altitude) for the Pandora tropo data
            if len(pandora2_day_data) <10:
                #Create empty rows at the end to populate
                empty_rows = pd.DataFrame(np.nan, index=range(10-len(pandora_day_data)), columns=pandora_split_dataframes[day].columns)
                #Append the empty rows to the DataFrame
                pandora2_day_data = pd.concat([pandora2_day_data, empty_rows], ignore_index=True)
                #then proceed to fill them
                pandora2_day_data['Pandora_alt'] = np.linspace(0, max(df['altitude']), len(pandora2_day_data))
            else: #proceed as normal if we have enough points
                pandora2_day_data['Pandora_alt'] = np.linspace(0, max(df['altitude']), len(pandora2_day_data))
                #also add a set of y's at 0 for the surface pandora estimatea
                surfpandora_day_data['Pandora_alt'] = np.linspace(0, 0, len(surfpandora_day_data))
                
        #Add a title with the date to each subplot
        axs[k].set_title('{}'.format(day), y=.9)  # Adjust the vertical position (0 to 1)
        axs[k].legend(loc='upper right', bbox_to_anchor=(1.0, 0.9))
     
    
        #then plot the flight data
        axs[k].scatter(df[' CH2O_ISAF'], df['altitude'], label='ISAF', color='black')
        #then plot the instep data
        axs[k].scatter(df['INSTEP HCHO'], df['INSTEP altitude'], label='INSTEP', color='red')
        
        #if pandora locations only
        if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
            #add in the regular & surface pandora data here
            #replace the tropo data with the median before plotting
            pandora2_day_data['Pandora Tropo HCHO'] = np.nanmedian(pandora2_day_data['Pandora Tropo HCHO'])
            axs[k].scatter(pandora2_day_data['Pandora Tropo HCHO'], pandora2_day_data['Pandora_alt'], label='Pandora Tropospheric Column', color='blue')
            axs[k].scatter(surfpandora_day_data['Pandora Surface HCHO'], surfpandora_day_data['Surface Pandora altitude'], label='Pandora Surface Estimate', color='green')
         
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
     
    #Set the font size of the tick labels
    axs[k].tick_params(axis='both', labelsize=12)
    #Standardize the axes
    axs[k].set_xlim(x_min, x_max)
    axs[k].set_ylim(y_min, y_max)
        
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
