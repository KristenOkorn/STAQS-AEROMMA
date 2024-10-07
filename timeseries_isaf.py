# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 15:25:45 2024

Timeseries of INSTEP, ISAF, and Pandora surface

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
locations = ['TMF','Caltech','Redlands','Whittier','AFRC']#'Whittier','AFRC'
pods = ['YPODA2','YPODG5','YPODL5','YPODA7','YPODR9']#

#pollutant?
pollutant = 'HCHO'

for n in range(len(locations)): 
    #-------------------------------------
    #load in the in-situ data - ISAF HCHO
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
    #convert altitude - file is off by a factor of 10
    isaf['altitude'] = isaf['altitude']/10
    
    #-------------------------------------
    #now load in the matching pod data - CH4
    podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\RB STAQS Field 2024'
    #get the filename for the pod
    podfilename = "{}_{}.csv".format(pods[n],pollutant)
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
    pod.columns.values[0] = 'INSTEP {}'.format(pollutant)
    #add a column for altitude - will all be 0
    pod['INSTEP altitude'] = 0
    
    #-------------------------------------
    #next load in the pandora surface csv's - skip for caltech & redlands
    if locations[n] != 'Redlands' and locations[n] != 'Caltech':
        surfpandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
        #get the filename for pandora
        surfpandorafilename = "{}_surface_extra_HCHO.csv".format(locations[n])
        #join the path and filename
        surfpandorafilepath = os.path.join(surfpandoraPath, surfpandorafilename)
        surfpandora = pd.read_csv(surfpandorafilepath,index_col=1)
        #Reset the seconds to zero in the index
        surfpandora.index = surfpandora.index.str.replace(r'\d{2}$', '00')
        #Convert the index to a DatetimeIndex
        surfpandora.index = pd.to_datetime(surfpandora.index)#rename index to datetime
        surfpandora = surfpandora.rename_axis('datetime')
        #Filter so that the lowest quality data is NOT included
        surfpandora = surfpandora.loc[surfpandora['quality_flag'] != 12]
        #hold onto the HCHO data and relevant parameters only
        surfpandora = surfpandora[['HCHO','temperature','top_height','max_vert_tropo']]
        #resample to minutely - since pod data will be minutely
        surfpandora = surfpandora.resample('T').mean()
        #Change the pollutant column name
        surfpandora.columns.values[0] = 'Pandora Surface HCHO'
        #remove any negatives
        surfpandora = surfpandora[surfpandora.iloc[:, 0] >= 0]
        #convert mol/m3 to ppb
        surfpandora['Pandora Surface HCHO'] = surfpandora['Pandora Surface HCHO']*0.08206*surfpandora['temperature']*(10**(9))/1000
        #remove spikes above 100
        surfpandora = surfpandora[surfpandora['Pandora Surface HCHO'] <= 100]
    
    #-------------------------------------
    #initialize figure - one plot for each location
    fig, axs = plt.subplots(1, 1, figsize=(8, 4))

    #create a regular set of y's (altitude) for the Pandora tropo data
    #df['Pandora_alt'] = np.linspace(0, max(df['altitude']), len(df))
    #also plot the pandora surface data if a pandora site
    if locations[n] == 'Whittier' or locations[n] == 'AFRC' or locations[n] == 'TMF':
        axs.plot(surfpandora.index, surfpandora['Pandora Surface {}'.format(pollutant)], label='Pandora Surface', color='purple')
    #then plot the instep data
    axs.plot(pod.index, pod['INSTEP {}'.format(pollutant)], label='INSTEP', color='red')
   #first plot the flight data
    axs.plot(isaf.index, isaf[' CH2O_ISAF'], label='Picarro', color='black')
    #Add a title with the date to each subplot
    #axs[k].set_title('{}'.format(day), y=.9)  # Adjust the vertical position (0 to 1)
    axs.legend(loc='upper right', bbox_to_anchor=(1.0, 0.9))
    
    # Set the font size of the tick labels
    axs.tick_params(axis='both', labelsize=12)
        
    #Increase vertical space between subplots
    #plt.subplots_adjust(hspace=0.2, top=0.9, bottom=0.05)  # You can adjust the value as needed
    #Single y-axis label for all subplots
    #fig.text(0.03, 0.5, 'Altitude (m)', va='center', rotation='vertical',fontsize=16)
    #Common y-axis label
    fig.text(0.03, 0.5, '{} (ppb)'.format(pollutant), va='center',rotation='vertical',fontsize=16)
    #axs[-1].set_xlabel('{} (ppm)'.format(pollutant), ha='center',fontsize=16)
    #Common x-axis label for all subplots
    axs.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%y %H'))  # Format the dates
    
    # Rotate the x-axis labels
    plt.xticks(rotation=45)
    #Add an overall title to the plot
    fig.text(0.5,0.91,'{}'.format(locations[n]), ha = 'center', fontsize=16, weight = 'bold')

    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\ISAF Outputs\\'
    
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'timeseries_isaf_{}_{}'.format(pollutant,locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)