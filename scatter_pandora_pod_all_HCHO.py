# -*- coding: utf-8 -*-
"""
Created on Mon Nov 27 12:26:57 2023

Scatter the Pandora surface estimates & INSTEP data - 1 plot per location
All available dates combined

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
locations = ['AFRC','Ames','Richmond','TMF','Whittier']
pods = ['YPODR9','YPODL6','YPODL1','YPODA2','YPODA7']
colors = ['b','g','r','c','m']


for n in range(len(locations)):
    #-------------------------------------
    #initialize figure
    fig4 = plt.figure(4)
    ax4 = plt.axes()
    #initialize our counter for how many samples we have
    num = 0
    
    #-------------------------------------
    #first load in the pandora csv's
    #pandoraPath = 'C:\\Users\\okorn\\Documents\\INSTEP Pandora Comparisons\\Pandora Surface Concentrations'
    pandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
    #get the filename for pandora
    pandorafilename = "{}_surface_HCHO.csv".format(locations[n])
    #join the path and filename
    pandorafilepath = os.path.join(pandoraPath, pandorafilename)
    pandora = pd.read_csv(pandorafilepath,index_col=1)
    #Reset the seconds to zero in the index
    pandora.index = pandora.index.str.replace(r'\d{2}$', '00')
    #Convert the index to a DatetimeIndex
    pandora.index = pd.to_datetime(pandora.index)#rename index to datetime
    pandora = pandora.rename_axis('datetime')
    #get rid of any blank columns
    pandora = pandora[['HCHO']]
    #resample to minutely - since pod data will be minutely
    pandora = pandora.resample('T').mean()
    #Change the pollutant column name
    pandora.columns.values[0] = 'Pandora Surface HCHO'
    #remove any negatives
    pandora = pandora[pandora.iloc[:, 0] >= 0]
    #-------------------------------------
    #now load in the matching pod data - HCHO
    #podPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\Field Data'
    podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\HCHO\\HCHO more fall data - fix A7 & cal'
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
    #resample to hourly - trying something
    #pod = pod.resample('H').mean()
    #-------------------------------------
    #merge our dataframes
    merge = pd.merge(pandora,pod,left_index=True, right_index=True)
    #remove missing values for ease of plotting
    merge = merge.dropna()
    
    #-------------------------------------
    #add the num of measurements to our counter
    num = len(merge)
    #add the new data to our scatterplot
    ax4.scatter(merge['INSTEP HCHO'], merge['Pandora Surface HCHO'],c=colors[n], s=25)

    #Final touches for plotting
    #fig4.tight_layout()  
    #Add x and y axis labels
    ax4.set_xlabel('INSTEP Surface HCHO (ppb)')
    ax4.set_ylabel('Pandora Surface HCHO (mol/m3)')

    #Add text in different colors
    ax4.text(0.525, 0.93, 'n = {}'.format(num), fontsize=12, color='black', transform=ax4.transAxes)

    #Adding a title to fig4
    fig4.suptitle('Pandora vs. INSTEP HCHO', y=.93)  # Adjust the vertical position (0 to 1)
    #Add a 1:1 line
    plt.plot([min(merge['INSTEP HCHO']), max(merge['INSTEP HCHO'])], [min(merge['Pandora Surface HCHO']), max(merge['Pandora Surface HCHO'])], color='black', linestyle='--', label='1:1 Line')
   
    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\Pandora Comparisons\\'
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'Pandora_INSTEP_scatter_{}'.format(locations[n]))
    # Save the figure to a filepath
    fig4.savefig(savePath)