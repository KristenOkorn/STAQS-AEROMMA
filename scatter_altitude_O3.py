
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
from matplotlib.lines import Line2D

#get the relevant location data for each
locations = ['TMF','Caltech','Redlands','Whittier','AFRC']#'Whittier','AFRC'
pods = ['YPODA2','YPODG5','YPODL5','YPODA7','YPODR9']#

#locations = ['TMF']
#pods = ['YPODA2']

#pollutant?
pollutant = 'O3'

#use interquartile range for Pandora instead of full range?
IQR = 'yes'

for n in range(len(locations)): 
    #-------------------------------------
    #load in the DC-8 in-situ data - NNOx O3
    nnoxPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\NNOX Outputs\\'
    #get the filename for the pod
    nnoxfilename = "NNOX_NO2_O3_{}.csv".format(locations[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    nnoxfilepath = os.path.join(nnoxPath, nnoxfilename)
    nnox = pd.read_csv(nnoxfilepath,index_col=0)  
    #remove any negatives
    nnox = nnox[nnox.iloc[:, 0] >= 0]
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    nnox.index = pd.to_datetime(nnox.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
    #convert altitude - file is off by a factor of 10
    nnox['altitude'] = nnox['altitude']/10
    #-------------------------------------
    # #next load in the pandora column csv's - skip for caltech & redlands
    # if locations[n] != 'Redlands' and locations[n] != 'Caltech':
    #     pandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
    #     #get the filename for pandora
    #     pandorafilename = "{}_column_extra_O3.csv".format(locations[n])
    #     #join the path and filename
    #     pandorafilepath = os.path.join(pandoraPath, pandorafilename)
    #     pandora = pd.read_csv(pandorafilepath,index_col=1)
    #     #Reset the seconds to zero in the index
    #     pandora.index = pandora.index.str.replace(r'\d{2}$', '00')
    #     #Convert the index to a DatetimeIndex
    #     pandora.index = pd.to_datetime(pandora.index)#rename index to datetime
    #     pandora = pandora.rename_axis('datetime')
    #     #resample to minutely - since pod data will be minutely
    #     pandora = pandora.resample('T').mean()
    #     #Change the pollutant column name
    #     pandora.columns.values[0] = 'Pandora Column O3'
    #     #remove any negatives
    #     pandora = pandora[pandora.iloc[:, 0] >= 0]
    #     #convert from mol/m2 to ppb
    #     pandora['Pandora Column O3'] = pandora['Pandora Column O3']*(pandora['top_height'])*0.08206*pandora['temperature']*(10**(9))/1000
    # #-------------------------------------
    #now load in the matching pod data - O3
    podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\RB STAQS Field 2024'
    #get the filename for the pod
    podfilename = "{}_O3.csv".format(pods[n])
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
    pod.columns.values[0] = 'INSTEP O3'
    #add a column for altitude - will all be 0
    pod['INSTEP altitude'] = 0
    #-------------------------------------
    #add the surface O3 for Redlands only
    if locations[n] == 'Redlands':
        #now load in the Redlands surface O3 data
        redsurfPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Redlands O3 AQMD Reference'
        #get the filename for the pod
        redsurffilename = "RedlandsO3.csv"
        #read in the first worksheet from the workbook myexcel.xlsx
        redsurffilepath = os.path.join(redsurfPath, redsurffilename)
        redsurf = pd.read_csv(redsurffilepath,index_col=0)  
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        redsurf.index = pd.to_datetime(redsurf.index,errors='coerce')
        #Change the pollutant column name
        redsurf.columns.values[0] = 'SCAQMD O3'
        #add a column for altitude - will all be 0
        redsurf['SCAQMD altitude'] = 0
    #repeat for TMF
    if locations[n] == 'TMF':
        #now load in the Redlands surface O3 data
        tmfsurfPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment'
        #get the filename for the pod
        tmfsurffilename = "TMFO3.csv"
        #read in the first worksheet from the workbook myexcel.xlsx
        tmfsurffilepath = os.path.join(tmfsurfPath, tmfsurffilename)
        tmfsurf = pd.read_csv(tmfsurffilepath,index_col=0)  
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        tmfsurf.index = pd.to_datetime(tmfsurf.index,errors='coerce')
        #Change the pollutant column name
        tmfsurf.columns.values[0] = '49i O3'
        #add a column for altitude - will all be 0
        tmfsurf['49i altitude'] = 0
    
    #merge our dataframes
    merge = pd.merge(nnox,pod,left_index=True, right_index=True)
    #if we have matching surface data, add it
    if locations[n] == 'Redlands':
        merge = pd.merge(merge,redsurf,left_index=True, right_index=True)
    elif locations[n] == 'TMF':
        merge = pd.merge(merge,tmfsurf,left_index=True, right_index=True)
    # #merge with pandora also - except for caltech & redlands
    # if locations[n] != 'Redlands' and locations[n] != 'Caltech':
    #     merge = pd.merge(merge,pandora,left_index=True, right_index=True)
    
    #     if IQR == 'yes':
    #         # Calculate the interquartile range (IQR) for the pandora
    #         q1 = merge['Pandora Column {}'.format(pollutant)].quantile(0.25)
    #         q3 = merge['Pandora Column {}'.format(pollutant)].quantile(0.75)
    #         iqr = q3 - q1
        
    #         #Set the y-limits based on the IQR
    #         x_min = q1 - 1.5 * iqr
    #         x_max = q3 + 1.5 * iqr
        
    #         #filter the dataframe based on the IQR
    #         merge = merge[(merge['Pandora Column {}'.format(pollutant)] >= x_min) & (merge['Pandora Column {}'.format(pollutant)] <= x_max)]
            
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
        
        #create a regular set of y's (altitude) for the Pandora data
        # df['Pandora_alt'] = np.linspace(0, max(df['altitude']), len(df))
    
        #first plot the flight data
        axs[k].scatter(df['O3_NNOx'], df['altitude'], label='NNOx', color='black')
        #then plot the instep data
        axs[k].scatter(df['INSTEP O3'], df['INSTEP altitude'], label='INSTEP', color='red')
        #plot the surface data, if any
        if locations[n] ==  'Redlands':
            axs[k].scatter(df['SCAQMD O3'], df['SCAQMD altitude'], label='SCAQMD', color='blue')
        elif locations[n] == 'TMF':
            axs[k].scatter(df['49i O3'], df['49i altitude'], label='49i', color='blue')
        #then plot the pandora data, if there is any
        # if locations[n] != 'Redlands' and locations[n] != 'Caltech':
        #     axs[k].scatter(df['Pandora Column O3'], df['Pandora_alt'], label='Pandora Column Column', color='blue')
        #     #Add a title with the date to each subplot
        axs[k].set_title('{}'.format(day), y=.9)  # Adjust the vertical position (0 to 1)
        axs[k].legend(loc='upper right', bbox_to_anchor=(1.0, 0.9))
        
        # Set the font size of the tick labels
        axs[k].tick_params(axis='both', labelsize=12)  # Adjust 12 to your desired font size
        
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.2, top=0.9, bottom=0.05)  # You can adjust the value as needed
    #Single y-axis label for all subplots
    fig.text(0.03, 0.5, 'Altitude (m)', va='center', rotation='vertical',fontsize=16)
    #Common x-axis label for all subplots
    #fig.text(0.5, 0.1, 'HCHO (ppb)', ha='center',fontsize=16)
    axs[-1].set_xlabel('O3 (ppb)', ha='center',fontsize=16)
    #Add an overall title to the plot
    fig.text(0.5,0.91,'{}'.format(locations[n]), ha = 'center', fontsize=16, weight = 'bold')

    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\O3 Plots\\'
    #Create the full path with the figure name
    #Create the full path with the figure name
    if IQR == 'yes':
        savePath = os.path.join(Spath,'altitude_O3_{}_IQR'.format(locations[n]))
    else:
        savePath = os.path.join(Spath,'altitude_O3_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)
