# -*- coding: utf-8 -*-
"""
Created on Fri Jan 05 13:02:17 2024

Timeseries plot of Pandora surface estimates & INSTEP data - 1 plot per location
All available dates combined
All subplots in 1 figure

Color by data flag & filter by data flag - doesn't include lowest quality data (12)

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
locations = ['AFRC','Ames','Richmond','TMF','Whittier']
pods = ['YPODR9','YPODL6','YPODL1','YPODA2','YPODA7']
#colors = ['b','g','r','c','m']

#tropo or surface?
measTyp = 'tropo'
#pollutant?
pollutant = 'NO2'
#unit?
unit = 'mol/m2' #surface = mol/m3 #tropo = mol/m2

#use interquartile range instead of full range?
IQR = 'yes'

#initialize figure
fig, ax = plt.subplots(len(locations), 1, figsize=(8, 2 * len(locations)))

for n in range(len(locations)): 
    #-------------------------------------
    #first load in the pandora csv's
    #pandoraPath = 'C:\\Users\\okorn\\Documents\\INSTEP Pandora Comparisons\\Pandora Surface Concentrations'
    pandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
    #get the filename for pandora
    pandorafilename = "{}_{}_extra_{}.csv".format(locations[n], measTyp, pollutant)
    #join the path and filename
    pandorafilepath = os.path.join(pandoraPath, pandorafilename)
    pandora = pd.read_csv(pandorafilepath,index_col=1)
    #Reset the seconds to zero in the index
    pandora.index = pandora.index.str.replace(r'\d{2}$', '00')
    #Convert the index to a DatetimeIndex
    pandora.index = pd.to_datetime(pandora.index)#rename index to datetime
    pandora = pandora.rename_axis('datetime')
    #get rid of any unnecessary columns
    pandora = pandora[['{}'.format(pollutant),'quality_flag']]
    #resample to minutely - since pod data will be minutely
    pandora = pandora.resample('T').mean()
    #Change the pollutant column name
    pandora.columns.values[0] = 'Pandora {} {}'.format(measTyp, pollutant)
    #remove any negatives
    pandora = pandora[pandora.iloc[:, 0] >= 0]
    
    #-------------------------------------
    #Replace the quality flags with their meaning
    quality_flag_mapping = {
        0: 'assured high quality',
        1: 'assured medium quality',
        2: 'assured low quality',
        10: 'not-assured high quality',
        11: 'not-assured medium quality',
        12: 'not-assured low quality'}

    #Create a custom color map for quality_flag
    color_map = {
        0: 'red',
        1: 'orange',
        2: 'green',
        10: 'blue',
        11: 'cyan',
        12: 'black'}
    #-------------------------------------
    #Filter so that the lowest quality data is NOT included
    filtered_pandora = pandora.loc[pandora['quality_flag'] != 12]
    
    # Filter data within the specified date range
    filtered_pandora = filtered_pandora[(filtered_pandora.index >= datetime(2023, 6, 1)) & (filtered_pandora.index <= datetime(2023, 12, 1))]
    
    
    
    if IQR == 'yes':
        # Calculate the interquartile range (IQR)
        q1 = filtered_pandora['Pandora {} {}'.format(measTyp, pollutant)].quantile(0.25)
        q3 = filtered_pandora['Pandora {} {}'.format(measTyp, pollutant)].quantile(0.75)
        iqr = q3 - q1
        
        #Set the y-limits based on the IQR
        y_min = q1 - 1.5 * iqr
        y_max = q3 + 1.5 * iqr
        
        #filter the dataframe based on the IQR
        filtered_pandora = filtered_pandora[(filtered_pandora['Pandora {} {}'.format(measTyp, pollutant)] >= y_min) & (filtered_pandora['Pandora {} {}'.format(measTyp, pollutant)] <= y_max)]
    
    #add the num of measurements to our counter
    num = len(filtered_pandora)
    #add the new data to our scatterplot
    for value, data in pandora.groupby('quality_flag'):
        subset = filtered_pandora[filtered_pandora['quality_flag'] == value]
        ax[n].scatter(subset.index, subset['Pandora {} {}'.format(measTyp, pollutant)], label=quality_flag_mapping[value], c=color_map[value], marker='o')
        #ax[n].plot(filtered_pandora.index, filtered_pandora['Pandora {} {}'.format(measTyp, pollutant)],c=pandora['quality_flag_description'].map(color_map))

    #Add text in different colors
    ax[n].text(0.85, 0.8, 'n = {}'.format(num), fontsize=12, color='black', transform=ax[n].transAxes)

    #Adding a title to fig4
    ax[n].set_title('{}'.format(locations[n]), y=.78)  # Adjust the vertical position (0 to 1)
    
    # Customize x-axis ticks to show only one label per month
    ax[n].xaxis.set_major_locator(mdates.MonthLocator())
    ax[n].xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    
   
#Increase vertical space between subplots
plt.subplots_adjust(hspace=0.5)  # You can adjust the value as needed
#Single y-axis label for all subplots
fig.text(0.03, 0.5, 'Pandora {} {} ({})'.format(measTyp, pollutant, unit), va='center', rotation='vertical')

# Adding legend
#fig.legend(labels=[f'{value}: {quality_flag_mapping[value]}' for value in color_map.keys()], title='Quality Flag', bbox_to_anchor=(1.05, 0.5), loc='center left')
fig.legend(labels=[f'{value}: {quality_flag_mapping[value]}' for value in color_map.keys()], 
           title='Quality Flag', 
           bbox_to_anchor=(1.05, 0.5), 
           loc='center left', 
           handles=[plt.Line2D([0], [0], marker='o', color='w', label=f'{value}: {quality_flag_mapping[value]}', markerfacecolor=color_map[value], markersize=10) for value in color_map.keys()])

#Display the plot
plt.show()

#save to a different folder so we don't confuse the script on the next iteration
Spath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\Pandora Comparisons\\'
#Create the full path with the figure name
if IQR == 'yes':
    savePath = os.path.join(Spath,'Pandora_timeseries_nolowQ_{}_{}_IQR'.format(pollutant,measTyp))
else:
    savePath = os.path.join(Spath,'Pandora_timeseries_nolowQ_{}_{}'.format(pollutant,measTyp))
#Save the figure to a filepath
fig.savefig(savePath)