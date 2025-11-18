# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 11:10:31 2025

Scatterplot of INSTEP and Pandora surface HCHO data
Takes into account uncertainty of each

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
color = ['red','blue','cyan']

pollutants = ['HCHO']

#initialize figure - 1 plot per location
fig, axs = plt.subplots(2, 2, figsize=(10, 8))
axs = axs.ravel()

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
    pod['Top HCHO'] = pod['INSTEP HCHO'] + pod['uncert']
    pod['Bottom HCHO'] = pod['INSTEP HCHO'] - pod['uncert']
    
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
    
    #now get the top & bottom values
    surfpandora['Pandora High HCHO'] = surfpandora['HCHO'] + surfpandora['surface_uncertainty']
    surfpandora['Pandora Low HCHO'] = surfpandora['HCHO'] - surfpandora['surface_uncertainty']
   
    #convert mol/m3 to ppb
    surfpandora['Pandora High HCHO'] = surfpandora['Pandora High HCHO']*0.08206*surfpandora['temperature']*(10**(9))/1000
    surfpandora['Pandora Low HCHO'] = surfpandora['Pandora Low HCHO']*0.08206*surfpandora['temperature']*(10**(9))/1000
    
    #-------------------------------------
    #Merge our AEROMMA data    
    #-------------------------------------
    merge = pd.merge_asof(pod, surfpandora, left_index=True, right_index=True, tolerance=pd.Timedelta('5T'),  direction='nearest')
    merge = merge.dropna()
    
    #-------------------------------------
    #Time to plot!     
    #-------------------------------------
    axs[n].scatter(merge['Top HCHO'], merge['Pandora High HCHO'], color=color[n])
    axs[n].scatter(merge['Bottom HCHO'], merge['Pandora Low HCHO'], color=color[n])
    
    #update scaling for some subplots
    if locations[n] == "Whittier":
        axs[n].set_ylim(0, 25)
    elif locations[n] == 'TMF':
        axs[n].set_ylim(0, 8)
        
    #Add a title with the location to each subplot
    axs[n].set_title('{}'.format(locations[n]), y=.9)  # Adjust the vertical position (0 to 1)
 
    #also add a line of best fit to each
    # m, b = np.polyfit(merge['INSTEP HCHO'], merge['Pandora Surface HCHO'], 1)
    # y_hat = (merge['INSTEP HCHO']*m) + b
    # #get the r2 to display on the plot
    # r2 = 1 - np.sum((merge['Pandora Surface HCHO'] - (m*merge['INSTEP HCHO'] + b))**2) / np.sum((merge['Pandora Surface HCHO'] - np.mean(merge['Pandora Surface HCHO']))**2)
    # #now plot it all together
    # axs[n].plot(merge['INSTEP HCHO'], m*merge['INSTEP HCHO'] + b, color="black", label=f"R²={r2:.2f})")
 
    #Now plot the legend
    axs[n].legend(loc='upper right', bbox_to_anchor=(1.0, 0.7)) 

#-----Finishing touches for the overall figure-----    
#Increase vertical space between subplots
plt.subplots_adjust(hspace=0.2, top=0.9, bottom=0.1)  # You can adjust the value as needed
#Single y-axis label for all subplots
fig.text(0.03, 0.5, 'Pandora Surface HCHO (mol/m2)', va='center', rotation='vertical',fontsize=16)
#Common x-axis label for all subplots
fig.text(0.5, 0.05, 'HCHO (ppb)', ha='center',fontsize=16)
#axs.set_xlabel('INSTEP HCHO (ppb)', ha='center',fontsize=16)
#Add an overall title to the plot
fig.text(0.5,0.91,'HCHO', ha = 'center', fontsize=16, weight = 'bold')

#Display the plot
plt.show()

#save to a different folder so we don't confuse the script on the next iteration
Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\O3 Plots\\'
#Create the full path with the figure name
savePath = os.path.join(Spath,'INSTEP vs Pandora Surface with uncertainty')
#Save the figure to a filepath
fig.savefig(savePath)
    