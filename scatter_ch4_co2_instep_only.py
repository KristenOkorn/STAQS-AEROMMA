# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 19:02:06 2025

XY Scatterplot of CH4 and CO2
INSTEP data ONLY for entire timeseries

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
locations = ['Whittier','AFRC','Caltech','TMF']
pods = ['YPODA7','YPODR9','YPODG5','YPODA2']
color = ['red','blue','green','cyan']

pollutants = ['CH4','CO2']

#initialize figure - 1 plot per location
fig, axs = plt.subplots(2, 2, figsize=(10, 8))
axs = axs.ravel()

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
    pod_data = pod_data.dropna()
     
    #-------------------------------------
    #Time to plot!     
    #-------------------------------------
    #Get global min/max to standardize x & y axes
    x_max = pod_data['INSTEP CO2'].max()
    y_max = pod_data['INSTEP CH4'].max()
    
    #and use 0 for all mins - 80s are so points don't get cut off at the edges
    x_min = pod_data['INSTEP CO2'].min()
    y_min = pod_data['INSTEP CH4'].min()
    
    # #override for certain locations
    if locations[n] == 'AFRC':
        y_max = 3
    elif locations[n] == 'Caltech':
        y_max = 3
    elif locations[n] == 'TMF':
        y_max = 5
    
    axs[n].scatter(pod_data['INSTEP CO2'], pod_data['INSTEP CH4'], label='INSTEP', color=color[n])
    
    #add a line of best fit to each
    m, b = np.polyfit(pod_data['INSTEP CO2'], pod_data['INSTEP CH4'], 1)  # slope, intercept
    axs[n].plot(pod_data['INSTEP CO2'], m*pod_data['INSTEP CO2'] + b, color='black')
    
    #Set the font size of the tick labels
    axs[n].tick_params(axis='both', labelsize=12)
    #Standardize the axes
    axs[n].set_xlim(x_min, x_max)
    axs[n].set_ylim(y_min, y_max)
    axs[n].autoscale(False)
    
    #Add a title with the date to each subplot
    axs[n].set_title('{}'.format(locations[n]), y=.9)  # Adjust the vertical position (0 to 1)
 
        
#-----Finishing touches for the overall figure-----    
#Increase vertical space between subplots
plt.subplots_adjust(hspace=0.3, top=0.9, bottom=0.05)  # You can adjust the value as needed
#Single y-axis label for all subplots
fig.text(0.03, 0.5, 'CH4 (ppm)', va='center', rotation='vertical',fontsize=16)
#Common x-axis label for all subplots
#axs[-1].set_xlabel('CH4 + HCHO (ppm)',fontsize=16)
fig.subplots_adjust(bottom=0.10)  # increase the bottom margin
fig.text(0.5, 0.04, 'CO2 (ppm)', ha='center', va='center', fontsize=16)

#Display the plot
plt.show()

#save to a different folder so we don't confuse the script on the next iteration
Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\INSTEP Plots\\'
#Create the full path with the figure name
savePath = os.path.join(Spath,'INSTEP_CH4_CO2')
#Save the figure to a filepath
fig.savefig(savePath)