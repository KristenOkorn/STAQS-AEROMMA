# -*- coding: utf-8 -*-
"""
Created on Wed Dec  6 18:51:12 2023

Timeseries of Pandora surface, column & INSTEP side by side

HCHO

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from datetime import datetime
from matplotlib.lines import Line2D
import matplotlib.dates as mdates

#get the relevant location data for each
locations = ['Whittier','AFRC','Ames','Richmond','TMF']
pods = ['YPODA7','YPODR9','YPODL6','YPODL1','YPODA2']
colors = ['c','b','g','r','m']

#use interquartile range for Pandora instead of full range?
IQR = 'yes'
pollutant = 'HCHO'

#initialize figure
fig4, ax4 = plt.subplots(len(locations), 3, figsize=(15, 15), gridspec_kw={'width_ratios': [3, 3, 3]})

for n in range(len(locations)): 
    #-------------------------------------
    #first load in the pandora tropo csv's - skip for caltech & redlands
    if locations[n] != 'Redlands' and locations[n] != 'Caltech':
        pandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
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
        #Filter so that the lowest quality data is NOT included
        pandora = pandora.loc[pandora['quality_flag'] != 12]
        #get rid of any blank columns
        pandora = pandora[['HCHO']]
        #resample to minutely - since pod data will be minutely
        pandora = pandora.resample('T').mean()
        #Change the pollutant column name
        pandora.columns.values[0] = 'Pandora Tropo HCHO'
        #remove any negatives
        pandora = pandora[pandora.iloc[:, 0] >= 0]
        #convert to ppb
        pandora['Pandora Tropo HCHO'] = pandora['Pandora Tropo HCHO']*0.08206*298*100
    #-------------------------------------
    #next load in the pandora surface csv's - skip for caltech & redlands
    if locations[n] != 'Redlands' and locations[n] != 'Caltech':
        surfpandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
        #get the filename for pandora
        surfpandorafilename = "{}_surface_HCHO.csv".format(locations[n])
        #join the path and filename
        surfpandorafilepath = os.path.join(surfpandoraPath, surfpandorafilename)
        surfpandora = pd.read_csv(surfpandorafilepath,index_col=1)
        #Reset the seconds to zero in the index
        surfpandora.index = surfpandora.index.str.replace(r'\d{2}$', '00')
        #Convert the index to a DatetimeIndex
        surfpandora.index = pd.to_datetime(surfpandora.index)#rename index to datetime
        surfpandora = surfpandora.rename_axis('datetime')
        #get rid of any blank columns
        surfpandora = surfpandora[['HCHO']]
        #resample to minutely - since pod data will be minutely
        surfpandora = surfpandora.resample('T').mean()
        #Change the pollutant column name
        surfpandora.columns.values[0] = 'Pandora Surface HCHO'
        #remove any negatives
        surfpandora = surfpandora[surfpandora.iloc[:, 0] >= 0]
        #convert mol/m3 to ppb
        surfpandora['Pandora Surface HCHO'] = surfpandora['Pandora Surface HCHO']*0.08206*298*1000000
    #-------------------------------------
    #now load in the matching pod data - HCHO
    #podPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\Field Data'
    podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\HCHO\\HCHO more fall data - fix cal'
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
    merge = pd.merge(merge,surfpandora,left_index=True, right_index=True)

    #remove missing values for ease of plotting
    merge = merge.dropna()
    
    if IQR == 'yes':
        # Calculate the interquartile range (IQR) for the tropo pandora
        q1 = merge['Pandora Tropo {}'.format(pollutant)].quantile(0.25)
        q3 = merge['Pandora Tropo {}'.format(pollutant)].quantile(0.75)
        iqr = q3 - q1
    
        #Set the y-limits based on the IQR
        x_min = q1 - 1.5 * iqr
        x_max = q3 + 1.5 * iqr
    
        #filter the dataframe based on the IQR
        merge = merge[(merge['Pandora Tropo {}'.format(pollutant)] >= x_min) & (merge['Pandora Tropo {}'.format(pollutant)] <= x_max)]
        
        #-------------------------------------------------------------
        # Calculate the interquartile range (IQR) for the surface pandora
        q1 = merge['Pandora Surface {}'.format(pollutant)].quantile(0.25)
        q3 = merge['Pandora Surface {}'.format(pollutant)].quantile(0.75)
        iqr = q3 - q1
    
        #Set the y-limits based on the IQR
        x_min = q1 - 1.5 * iqr
        x_max = q3 + 1.5 * iqr
    
        #filter the dataframe based on the IQR
        merge = merge[(merge['Pandora Surface {}'.format(pollutant)] >= x_min) & (merge['Pandora Surface {}'.format(pollutant)] <= x_max)]

    #-------------------------------------
    #limit to just the summer data
    merge['date'] = merge.index
    merge = merge[(merge['date'].dt.month >= 7) & (merge['date'].dt.month <= 8)]

    #make the timeseries plots
    ax4[n,0].plot(merge.index, merge['Pandora Tropo HCHO'],c='b')
    ax4[n,1].plot(merge.index, merge['Pandora Surface HCHO'],c='g')
    ax4[n,2].plot(merge.index, merge['INSTEP HCHO'],c='r')
    
    # Format x-axis as month
    ax4[n,0].xaxis.set_major_locator(mdates.MonthLocator())
    ax4[n,0].xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax4[n,1].xaxis.set_major_locator(mdates.MonthLocator())
    ax4[n,1].xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax4[n,2].xaxis.set_major_locator(mdates.MonthLocator())
    ax4[n,2].xaxis.set_major_formatter(mdates.DateFormatter('%b'))

    # Set the font size of the tick labels
    ax4[n,0].tick_params(axis='both', labelsize=12)  # Adjust 12 to your desired font size
    ax4[n,1].tick_params(axis='both', labelsize=12)
    ax4[n,2].tick_params(axis='both', labelsize=12)
    
    #add a y-axis subheading with each location
    #ax4[n,2].set_ylabel('{}'.format(locations[n]), rotation=0, labelpad=15) 

#Adding a title to each column of subplots
ax4[0,0].set_title('Pandora Troposheric HCHO', y=.96, fontsize=16)  # Adjust the vertical position (0 to 1)
ax4[0,1].set_title('Pandora Surface HCHO', y=.96, fontsize=16)  # Adjust the vertical position (0 to 1)
ax4[0,2].set_title('INSTEP HCHO', y=.96, fontsize=16)  

#just for AGU - add a y-axis label to the first plot
fig4.text(0.08, 0.82, 'HCHO (ppb)', va='center', rotation='vertical', fontsize=16) 

#Increase vertical space between subplots
plt.subplots_adjust(hspace=0.2)  # You can adjust the value as needed
#Single y-axis label for all subplots
#fig4.text(0.08, 0.5, 'HCHO (ppb)', va='center', rotation='vertical',fontsize=16)

#Display the plot
plt.show()

#save to a different folder so we don't confuse the script on the next iteration
Spath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\Pandora Comparisons\\'
#Create the full path with the figure name
#Create the full path with the figure name
if IQR == 'yes':
    savePath = os.path.join(Spath,'Pandora_INSTEP_timeseries_HCHO_IQR')
else:
    savePath = os.path.join(Spath,'Pandora_INSTEP_scatter_HCHO')
#Save the figure to a filepath
fig4.savefig(savePath)