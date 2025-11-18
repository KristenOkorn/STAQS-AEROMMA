# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 13:52:52 2024

Timeseries plot of Picarro, INSTEP, & TCCON

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
pollutant = 'CH4'

for n in range(len(locations)): 
    #-------------------------------------
    #load in the PICARRO data
    picarroPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\Picarro CO2 CH4 CO\\'
    #get the filename for the pod
    picarrofilename = "Picarro_CH4_CO2_{}.csv".format(locations[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    picarrofilepath = os.path.join(picarroPath, picarrofilename)
    picarro = pd.read_csv(picarrofilepath,index_col=0)  
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    picarro.index = pd.to_datetime(picarro.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
   
    #convert altitude - file is off by a factor of 10
    picarro['altitude'] = picarro['altitude']/10
    
    #Convert ppb to ppm if CH4 or CO
    if pollutant == 'CH4' or pollutant == 'CO':
        picarro['{}_ppb'.format(pollutant)] = picarro['{}_ppb'.format(pollutant)]/1000
        #also get rid of missing data
        picarro = picarro[picarro['{}_ppb'.format(pollutant)] >= 0]
    else:
        #remove the negatives regardless
        picarro = picarro[picarro['{}_ppm'.format(pollutant)] >= 0]
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
    #now load in the matching TCCON data - if a tccon site
    if locations[n] == 'Caltech' or locations[n] == 'AFRC':
        tcconPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\TCCON'
        #get the filename for the tccon data
        tcconfilename = "{}_TCCON.csv".format(locations[n])
        #read in the first worksheet from the workbook myexcel.xlsx
        tcconfilepath = os.path.join(tcconPath, tcconfilename)
        tccon = pd.read_csv(tcconfilepath,index_col=0)  
        #keep just the column we need
        tccon = tccon['{}'.format(pollutant)].to_frame()
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        tccon.index = pd.to_datetime(tccon.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
        #resample to minutely
        tccon = tccon.resample('T').median()
        #Change the pollutant column name
        tccon.rename(columns={'{}'.format(pollutant): 'TCCON {}'.format(pollutant)}, inplace=True)

    #-------------------------------------
    #initialize figure - one plot for each location
    fig, axs = plt.subplots(1, 1, figsize=(8, 4))

    #create a regular set of y's (altitude) for the Pandora tropo data
    #df['Pandora_alt'] = np.linspace(0, max(df['altitude']), len(df))
    
    #then plot the instep data
    axs.plot(pod.index, pod['INSTEP {}'.format(pollutant)], label='INSTEP', color='red')
    #also plot the tccon data if a tccon site
    if locations[n] == 'Caltech' or locations[n] == 'AFRC':
        axs.plot(tccon.index, tccon['TCCON {}'.format(pollutant)], label='TCCON', color='purple')
    #first plot the flight data
    if pollutant == 'CO2':
        axs.plot(picarro.index, picarro['{}_ppm'.format(pollutant)], label='Picarro', color='black')
    else:
        axs.plot(picarro.index, picarro['{}_ppb'.format(pollutant)], label='Picarro', color='black')
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
    if pollutant == 'CO2':
        fig.text(0.03, 0.5, '{} (ppm)'.format(pollutant), va='center',rotation='vertical',fontsize=16)
    else:
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
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\TCCON Plots\\'
    
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'timeseries_tccon_{}_{}'.format(pollutant,locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)