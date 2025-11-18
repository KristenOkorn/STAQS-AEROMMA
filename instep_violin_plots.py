# -*- coding: utf-8 -*-
"""
Created on Fri Oct  3 11:40:34 2025

Violin plots of INSTEP data

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os

#get the relevant location data for each
locations = ['Whittier','AFRC','TMF','Caltech','Redlands'] #redlands
pods = ['YPODA7','YPODR9','YPODA2','YPODG5','YPODL5'] #l5
colors = ["salmon", "skyblue", "lightgreen", '#f4a261','plum'] #plum
pollutants = ['O3','CO2']

#-------------------------------------
#Load in the pod data
for pollutant in pollutants:
    
    #initialize figure - 1 plot per location
    fig, axs = plt.subplots(1,1, figsize=(10, 8))
    
    #overarching df to hold all location data for this pollutant
    pod_data = pd.DataFrame()
    #now loop through each pollutant for this pod
    
    #also get the units for plotting later
    if pollutant == 'O3' or pollutant == 'HCHO':
        unit = 'ppb'
    else:
        unit = 'ppm'
        
    for n in range(len(locations)): 
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
        pod.columns.values[0] = '{}'.format(locations[n])
        
        #need to make these columns in a dataframe after loading them in
        if pod_data.empty:
            pod_data = pod
        else:
            pod_data = pod_data.join(pod, how='outer', lsuffix='_1', rsuffix='_2')
    
    pod_data = pod_data.apply(pd.to_numeric, errors="coerce")
   
    #Convert to list for plotting
    data = [pod_data[col].dropna().values for col in pod_data.columns]
    #-------------------------------------
    #Time to plot!     
    #-------------------------------------
    sc = axs.violinplot(data, showmeans=True, showmedians=True)
    
    # Assign different colors
    for pc, color in zip(sc['bodies'], colors):
        pc.set_facecolor(color)
        pc.set_edgecolor("black")
        pc.set_alpha(0.7)
   
    #Set the font size of the tick labels
    axs.tick_params(axis='both', labelsize=12)
  
    #-----Finishing touches for the overall figure-----    
    axs.set_xticks(range(1, len(pod_data.columns) + 1))
    axs.set_xticklabels(pod_data.columns)
    axs.set_ylabel("{} ({})".format(pollutant,unit))
    axs.set_title("{}".format(pollutant))
    
    #adjust axes for methane only
    if pollutant == 'CH4':
        axs.set_ylim(1, 4)
    #Display the plot
    plt.show()
    
    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\INSTEP Plots\\'
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'INSTEP_{}_violin'.format(pollutant))
    #Save the figure to a filepath
    fig.savefig(savePath)
