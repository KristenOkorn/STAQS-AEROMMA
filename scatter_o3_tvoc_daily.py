# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 13:18:57 2025

Make XY scatterplots of ozone and VOC (HCHO + CH4)
Try both overall plots & per day
Split by location

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
locations = ['Whittier','AFRC','Caltech']
pods = ['YPODA7','YPODR9','YPODG5']

pollutants = ['O3','HCHO','CH4']

#-------------------------------------
#Load in the pod data - need O3, HCHO, and CH4
for n in range(len(locations)): 
    #overarching df to hold all pollutant data for this pod
    pod_data = pd.DataFrame()
    #now loop through each pollutant for this pod
    for pollutant in pollutants:
        podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\R1 STAQS Field'
        #get the filename for the pod
        podfilename = "{}_{}_field_corrected.csv".format(pods[n],pollutant)
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
        pod.columns.values[0] = 'INSTEP {}'.format(pollutant)
        #convert ppb to ppm for HCHO
        if pollutant == 'HCHO':
            pod['INSTEP HCHO'] = pod['INSTEP HCHO']/1000
        
        #need to make these columns in a dataframe after loading them in
        if pod_data.empty:
            pod_data = pod
        else:
            pod_data = pod_data.join(pod, how='outer', lsuffix='_1', rsuffix='_2')
    
    pod_data = pod_data.apply(pd.to_numeric, errors="coerce")
    #-------------------------------------
    #Load in the AEROMMA airborne data - need O3, HCHO, and CH4        
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
    #re-average to minute to match pod
    cl = cl.resample('1T').mean()
    
    #load in the DC-8 in-situ data - Picarro CH4
    picarroPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\Picarro CO2 CH4 CO\\'
    #get the filename for the pod
    picarrofilename = "Picarro_CH4_CO2_{}.csv".format(locations[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    picarrofilepath = os.path.join(picarroPath, picarrofilename)
    picarro = pd.read_csv(picarrofilepath,index_col=0)  
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    picarro.index = pd.to_datetime(picarro.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
    #split into separate ch4 file - helpful for handling missing data
    picarroch4 = picarro
    #remove any negatives for CH4 specifically
    picarroch4 = picarroch4[picarroch4['CH4_ppb'] >= 0]
    #Convert ppb to ppm for CH4
    picarroch4['CH4_ppm'] = picarroch4['CH4_ppb']/1000
    
    #load in the DC-8 in-situ data - ISAF HCHO
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
    #now convert ppb to ppm
    isaf[' CH2O_ISAF'] = isaf[' CH2O_ISAF']/1000
    
    #-------------------------------------
    #Merge our AEROMMA data and get tVOC proxy from it        
    #-------------------------------------
    merge = pd.merge_asof(cl, picarroch4, left_index=True, right_index=True, tolerance=pd.Timedelta('5T'),  direction='nearest')  
    merge = pd.merge_asof(merge, isaf, left_index=True, right_index=True, tolerance=pd.Timedelta('5T'),  direction='nearest')
    
    merge['DC8 tVOC'] = merge[' CH2O_ISAF'] + merge['CH4_ppm']
    pod_data['INSTEP tVOC'] = pod_data['INSTEP CH4'] + pod_data['INSTEP HCHO']
    
    merge = merge.dropna()
    
    megamerge = merge.join(pod_data, how='outer', lsuffix='_1', rsuffix='_2')

    #-------------------------------------
    #Separating into unique days and axis limits       
    #-------------------------------------
    #Create a dictionary to store DataFrames for each unique day
    split_dataframes = {}
    #Get global min/max to standardize x & y axes
    x_max = math.ceil(max(merge['DC8 tVOC'].max(), pod_data['INSTEP tVOC'].max()))
    y_max = math.ceil(max(merge['O3_CL'].max(), pod_data['INSTEP O3'].max()))
    
    #and use 0 for all mins - 80s are so points don't get cut off at the edges
    x_min = math.ceil(min(merge['DC8 tVOC'].min(), pod_data['INSTEP tVOC'].min()))
    y_min = math.ceil(min(merge['O3_CL'].min(), pod_data['INSTEP O3'].min()))
    
    #override for certain locations
    if locations[n] == 'AFRC' or locations[n] == 'Caltech':
        x_max = 3
    #-------------------------------------
    #figure out how many days we have - for how many subplots
    num_unique_days = len(np.unique(merge.index.date))
    #also get the list of them to split by
    unique_days_list = np.unique(merge.index.date).tolist()
    
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(num_unique_days, 1, figsize=(8, 4 * num_unique_days))
    
    # If there is only one subplot, make it a list to handle indexing
    if num_unique_days == 1:
        axs = [axs]
    
    #-------------------------------------
    #Plotting - for each day       
    #-------------------------------------
    
    #Split the DataFrame based on unique days
    for day in unique_days_list:
        day_data = megamerge[megamerge.index.date == day]
        split_dataframes[day] = day_data
    
        #plot the airborne and INSTEP data
        for k, (day, df) in enumerate(split_dataframes.items()):
            axs[k].scatter(df['INSTEP tVOC'], df['INSTEP O3'], label='INSTEP', color='red')
            axs[k].scatter(df['DC8 tVOC'], df['O3_CL'], label='Airborne', color='black')
            
            #Set the font size of the tick labels
            axs[k].tick_params(axis='both', labelsize=12)
            #Standardize the axes
            axs[k].set_xlim(x_min, x_max)
            axs[k].set_ylim(y_min, y_max)
            axs[k].autoscale(False)
            
        #---- Finishing touches for each subplot-----
        #Now plot the legend
        axs[k].legend(loc='upper right', bbox_to_anchor=(1.0, 0.7)) 
        #Add a title with the date to each subplot
        axs[k].set_title('{}'.format(day), y=.9)  # Adjust the vertical position (0 to 1)
     
    #-----Finishing touches for the overall figure-----    
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.2, top=0.9, bottom=0.05)  # You can adjust the value as needed
    #Single y-axis label for all subplots
    fig.text(0.03, 0.5, 'O3 (ppb)', va='center', rotation='vertical',fontsize=16)
    #Common x-axis label for all subplots
    #fig.text(0.5, 0.1, 'HCHO (ppb)', ha='center',fontsize=16)
    axs[-1].set_xlabel('CH4 + HCHO (ppm)', ha='center',fontsize=16)
    #Add an overall title to the plot
    fig.text(0.5,0.91,'{}'.format(locations[n]), ha = 'center', fontsize=16, weight = 'bold')
    
    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\O3 Plots\\'
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'O3_tVOC_daily_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)
    