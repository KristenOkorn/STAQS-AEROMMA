# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 16:06:02 2025

Make XY scatterplots of ozone and HCHO
data from all matching days one one plot

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

pollutants = ['O3','HCHO']

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
    
    #-------------------------------------
    #Merge our AEROMMA data    
    #-------------------------------------
    merge = pd.merge_asof(cl, isaf, left_index=True, right_index=True, tolerance=pd.Timedelta('5T'),  direction='nearest')
    merge = merge.dropna()
    
    #-------------------------------------
    #limit the INSTEP data to the same time ranges as the DC8 data
    #-------------------------------------
    # Find contiguous blocks in df1
    gaps = merge.index.to_series().diff() > pd.Timedelta("1H")  # detect gaps > 1 hour
    group = gaps.cumsum()  # group each continuous block

    pod_blocks = []
    for _, block in merge.groupby(group):
        start, end = block.index.min(), block.index.max()
        pod_blocks.append(pod_data.loc[(pod_data.index >= start) & (pod_data.index <= end)])

    pod_limited = pd.concat(pod_blocks)

    #-------------------------------------
    #Time to plot!     
    #-------------------------------------
    #Get global min/max to standardize x & y axes
    x_max = math.ceil(max(merge[' CH2O_ISAF'].max(), pod_limited['INSTEP HCHO'].max()))
    y_max = math.ceil(max(merge['O3_CL'].max(), pod_limited['INSTEP O3'].max()))
    
    #and use 0 for all mins - 80s are so points don't get cut off at the edges
    x_min = math.ceil(min(merge[' CH2O_ISAF'].min(), pod_limited['INSTEP HCHO'].min()))
    y_min = math.ceil(min(merge['O3_CL'].min(), pod_limited['INSTEP O3'].min()))
    
    #override for certain locations
    # if locations[n] == 'AFRC' or locations[n] == 'Caltech':
    #     x_max = 3
    
    #initialize figure - 1 plot per location
    fig, axs = plt.subplots(1, 1, figsize=(8, 4))
    
    #limit INSTEP to the same dates & time ranges as the DC8 data 
    
    
    axs.scatter(pod_limited['INSTEP HCHO'], pod_limited['INSTEP O3'], label='INSTEP', color='red')
    axs.scatter(merge[' CH2O_ISAF'], merge['O3_CL'], label='Airborne', color='black')
    
    #Set the font size of the tick labels
    axs.tick_params(axis='both', labelsize=12)
    #Standardize the axes
    axs.set_xlim(x_min, x_max)
    axs.set_ylim(y_min, y_max)
    axs.autoscale(False)
        
    #---- Finishing touches for each subplot-----
    #Now plot the legend
    axs.legend(loc='upper right', bbox_to_anchor=(1.0, 0.7)) 
   
    #-----Finishing touches for the overall figure-----    
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.2, top=0.9, bottom=0.05)  # You can adjust the value as needed
    #Single y-axis label for all subplots
    fig.text(0.03, 0.5, 'O3 (ppb)', va='center', rotation='vertical',fontsize=16)
    #Common x-axis label for all subplots
    #fig.text(0.5, 0.1, 'HCHO (ppb)', ha='center',fontsize=16)
    axs.set_xlabel('HCHO (ppb)', ha='center',fontsize=16)
    #Add an overall title to the plot
    fig.text(0.5,0.91,'{}'.format(locations[n]), ha = 'center', fontsize=16, weight = 'bold')
    
    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\O3 Plots\\'
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'O3_HCHO_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)
    