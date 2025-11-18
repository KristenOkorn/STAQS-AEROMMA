# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 15:10:05 2025

INSTEP and Pandora split by day with errorbars

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

#get the relevant location data for each
locations = ['Whittier','AFRC','TMF']
pods = ['YPODA7','YPODR9','YPODA2']
color = ["salmon", "skyblue", "lightgreen"]

pollutants = ['HCHO']

#initialize figure - 1 plot per location
fig, axs = plt.subplots(2,3, figsize=(10, 3))
#axs = axs.ravel()

#-------------------------------------
#Load in the pod data - HCHO
for n in range(len(locations)): 

    #-------------------------------------
    #Load in the pod data  
    #-------------------------------------
    podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\R1 STAQS Field'
    #get the filename for the pod
    podfilename = "{}_HCHO_field_corrected.csv".format(pods[n])
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
    pod.columns.values[0] = 'INSTEP HCHO'
    
    #now get the top & bottom values
    pod['uncert'] = pod['INSTEP HCHO']*0.4
    
    #split by date
    pod = pod.resample('D').median()
    
    #-------------------------------------
    #Load in the Pandora surface data      
    #-------------------------------------
    #now load in the pandora data
    pandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
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
    #surfpandora = surfpandora.loc[surfpandora['quality_flag'] != 12]
    
    #for additional filtering, get the high quality data alone
    pandora_high = surfpandora[surfpandora['quality_flag'] == 10]
    #now get the mean indep uncertainty for the high values
    high_mean = pandora_high['surface_uncertainty'].mean()
    #and the standard deviation
    high_std = pandora_high['surface_uncertainty'].std()
    #now calculate the cut-off value from this
    cutoff = high_mean + (3*high_std)
    #now apply this filtering as a new dataframe
    surfpandora = surfpandora[surfpandora['surface_uncertainty'] < cutoff]
    
    #also drop negatives - negatives in uncert means no uncert determined
    surfpandora.loc[surfpandora['HCHO'] < 0, 'HCHO'] = 0
    surfpandora.loc[surfpandora['surface_uncertainty'] < 0, 'surface_uncertainty'] = 0
    
    #convert mol/m3 to ppb
    surfpandora['HCHO'] = surfpandora['HCHO']*0.08206*surfpandora['temperature']*(10**(9))/1000
    surfpandora['surface_uncertainty'] = surfpandora['surface_uncertainty']*0.08206*surfpandora['temperature']*(10**(9))/1000
    
    #daily resample
    surfpandora = surfpandora.resample('D').median()
    
    #-------------------------------------
    #Time to plot!     
    #-------------------------------------
    #Add errorbars for uncertainty
    axs[0,n].errorbar(pod.index, pod['INSTEP HCHO'], yerr=pod['uncert'], fmt='o', color='black',ecolor=color[n], capsize=1)
    axs[1,n].errorbar(surfpandora.index, surfpandora['HCHO'], yerr=surfpandora['surface_uncertainty'], fmt='o', color='black',ecolor=color[n], capsize=1)  
        
    #Add a title with the location to each subplot
    axs[0,n].set_title('{}'.format(locations[n]), y=1,fontweight='bold')  # Adjust the vertical position (0 to 1)

#-----Finishing touches for the overall figure-----    
#Increase vertical space between subplots
plt.subplots_adjust(hspace=0.35, top=0.9, bottom=0.15)  # You can adjust the value as needed
#Single y-axis label for all top subplots
fig.text(0.095, 0.75, 'INSTEP HCHO (ppb)', va='center', rotation='vertical',fontsize=8)
fig.text(0.095, 0.25, 'Pandora HCHO (ppb)', va='center', rotation='vertical',fontsize=8)
#Common x-axis label for all subplots
#fig.text(0.5, 0.005, 'Day', ha='center',fontsize=12)

#Display the plot
plt.show()

#save to a different folder so we don't confuse the script on the next iteration
Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\O3 Plots\\'
#Create the full path with the figure name
savePath = os.path.join(Spath,'INSTEP and Pandora Surface days with errorbars daily')
#Save the figure to a filepath
fig.savefig(savePath)
    