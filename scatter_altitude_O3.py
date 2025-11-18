
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  6 20:11:13 2023
Altitude plot of DC-8, Pandora, & pod
+Ozone data from NNOx, no surface pandora estimate
Column Pandora, not tropo - tropo not available

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from datetime import datetime
import math

#get the relevant location data for each
locations = ['Redlands','Whittier']
pods = ['YPODL5','YPODA7']

#pollutant?
pollutant = 'O3'

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

        #----------
        #merge the pandora temperature with the pandora data (as of merge to find nearest rather than exact match)
        pmerge = pd.merge_asof(pandora, temp, left_index=True, right_index=True, tolerance=pd.Timedelta('1H'),  direction='nearest')  
        
        #convert from mol/m2 to ppb - use 50km as top of stratosphere
        pmerge['Pandora Column O3'] = pmerge['O3']*0.08206*pmerge['temp_K']*1000/(50000)
        
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
    
    #-------------------------------------
    #'as of' merge - just to match up the time windows, not the exact times
    merges = pd.merge_asof(cl, pod, left_index=True, right_index=True, tolerance=pd.Timedelta('1H'),  direction='nearest')  
    #drop missing values
    merges = merges.dropna()         
    #-------------------------------------
    
    if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
        #filter to match times for pandora also - get the start and end times from the merge file
        start_time = cl.index[0]
        end_time = cl.index[-1]
        #now filter pandora based on this
        pmerge = pmerge[(pmerge.index >= start_time) & (pmerge.index <= end_time)]
        #remove missing values for ease of plotting
        pmerge = pmerge.dropna()
    
    #-------------------------------------
    
    #Create a dictionary to store DataFrames for each unique day
    split_dataframes = {}
    pandora_split_dataframes = {}
    
    #-------------------------------------    
    #Get global min/max to standardize x & y axes
    x_max = math.ceil(max(merges['O3_CL'].max(), merges['INSTEP O3'].max()))
    y_max = math.ceil(merges['altitude'].max() +80)
    
    #and use 0 for all mins - 80s are so points don't get cut off at the edges
    x_min = 0
    y_min = -80
    
    #-------------------------------------
    #figure out how many days we have - for how many subplots
    num_unique_days = len(np.unique(cl.index.date))
    #also get the list of them to split by
    unique_days_list = np.unique(cl.index.date).tolist()
    
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(num_unique_days, 1, figsize=(8, 4 * num_unique_days))
    
    # If there is only one subplot, make it a list to handle indexing
    if num_unique_days == 1:
        axs = [axs]
    
    #-------------------------------------
    
    #Split the DataFrame based on unique days
    for day in unique_days_list:
        day_data = cl[cl.index.date == day]
        split_dataframes[day] = day_data
    
        if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
            #now repeat for the pandora data
            pandora_day_data = pmerge[pmerge.index.date == day]
            pandora_split_dataframes[day] = pandora_day_data
    
            #create columns as needed for pandora data
            for k, (day, df) in enumerate(pandora_split_dataframes.items()):
                if locations[n] == 'Whittier' or locations[n] == 'TMF' or locations[n] == 'AFRC':
                    # Get daily data for Pandora and surface
                    pandora_day_data = pandora_split_dataframes.get(day)
                    
                    #create a regular set of y's (altitude) for the Pandora tropo data
                    df['altitude'] = np.linspace(0, y_max, len(df))
                    #now median
                    df['Pandora Column O3'] = np.nanmedian(df['Pandora Column O3'])
                    #and create a linspace of only 15 points so its not too crowded on the plot
                    lin_hcho = df.iloc[np.linspace(0, len(df) - 1, 15, dtype=int)]['Pandora Column O3']
                    lin_alt = df.iloc[np.linspace(0, len(df) - 1, 15, dtype=int)]['altitude']
                    #now plot the pandora tropo data
                    axs[k].scatter(lin_hcho, lin_alt, label='Pandora Column O3', color='blue')
                    
        #then plot the flight data
        for k, (day, df) in enumerate(split_dataframes.items()):
            axs[k].scatter(df['O3_CL'], df['altitude'], label='Chemiluminescence', color='black')
        
            #then plot the instep data
            pod_filtered = pod[(pod.index >= df.index.min()) & (pod.index <= df.index.max())]
            axs[k].scatter(pod_filtered['INSTEP O3'], pod_filtered['INSTEP altitude'], label='INSTEP', color='magenta')
            
            #Set the font size of the tick labels
            axs[k].tick_params(axis='both', labelsize=12)
            #Standardize the axes
            axs[k].set_xlim(x_min, x_max)
            axs[k].set_ylim(y_min, y_max)
            axs[k].autoscale(False)
            
            #nov25 version - individual x&y axis labels for each subplot
            axs[k].set_xlabel('O3 (ppb)')
            axs[k].set_ylabel('Altitude (m)')
            
        #---- Finishing touches for each subplot-----
        #Now plot the legend
        axs[k].legend(loc='upper right', bbox_to_anchor=(1.0, 0.7)) 
        #Add a title with the date to each subplot
        axs[k].set_title('{} - {}'.format(locations[n], day), y=.9)  # Adjust the vertical position (0 to 1)
     
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
    savePath = os.path.join(Spath,'altitude_O3_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)