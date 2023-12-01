# -*- coding: utf-8 -*-
"""
Created on Wed Nov 29 09:38:43 2023
Scatter the pandora data against the INSTEP 

@author: okorn
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Nov 28 13:02:17 2023

Scatter the Pandora surface estimates & INSTEP data - 1 plot per location
All available dates combined
All subplots in 1 figure
Compare Pandora NO2 with INSTEP O3

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
locations = ['AFRC','Ames','Richmond','TMF','Whittier', 'SJSU']
pods = ['YPODR9','YPODL6','YPODL1','YPODA2','YPODA7','YPODL9']
colors = ['b','g','r','c','m','y']

#tropo or surface?
measTyp = 'tropo'

#pandora unit?
unit = 'mol/m2' #surface = mol/m3 #tropo = mol/m2

#use interquartile range for Pandora instead of full range?
IQR = 'yes'

#initialize figure
fig4, ax4 = plt.subplots(len(locations), 1, figsize=(8, 4 * len(locations)))

for n in range(len(locations)): 
    #-------------------------------------
    #first load in the pandora csv's
    #pandoraPath = 'C:\\Users\\okorn\\Documents\\INSTEP Pandora Comparisons\\Pandora Surface Concentrations'
    pandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
    #get the filename for pandora
    pandorafilename = "{}_{}_NO2.csv".format(locations[n],measTyp)
    #join the path and filename
    pandorafilepath = os.path.join(pandoraPath, pandorafilename)
    pandora = pd.read_csv(pandorafilepath,index_col=1)
    #Reset the seconds to zero in the index
    pandora.index = pandora.index.str.replace(r'\d{2}$', '00')
    #Convert the index to a DatetimeIndex
    pandora.index = pd.to_datetime(pandora.index)#rename index to datetime
    pandora = pandora.rename_axis('datetime')
    #get rid of any blank columns
    pandora = pandora[['NO2']]
    #resample to minutely - since pod data will be minutely
    pandora = pandora.resample('T').mean()
    #Change the pollutant column name
    pandora.columns.values[0] = 'Pandora {} NO2'.format(measTyp)
    #remove any negatives
    pandora = pandora[pandora.iloc[:, 0] >= 0]
    #-------------------------------------
    #now load in the matching pod data - O3
    #podPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\Field Data'
    podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Ozone\\Ozone more fall data'
    #get the filename for the pod
    podfilename = "{}_O3.csv".format(pods[n])
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
    pod.columns.values[0] = 'INSTEP O3'
    #resample to hourly - trying something
    #pod = pod.resample('H').mean()
    #-------------------------------------
    #merge our dataframes
    merge = pd.merge(pandora,pod,left_index=True, right_index=True)
    #remove missing values for ease of plotting
    merge = merge.dropna()
    
    if IQR == 'yes':
        # Calculate the interquartile range (IQR)
        q1 = merge['Pandora {} NO2'.format(measTyp)].quantile(0.25)
        q3 = merge['Pandora {} NO2'.format(measTyp)].quantile(0.75)
        iqr = q3 - q1
        
        #Set the y-limits based on the IQR
        y_min = q1 - 1.5 * iqr
        y_max = q3 + 1.5 * iqr
        
        #filter the dataframe based on the IQR
        merge = merge[(merge['Pandora {} NO2'.format(measTyp)] >= y_min) & (merge['Pandora {} NO2'.format(measTyp)] <= y_max)]
    
    #-------------------------------------
    #add the num of measurements to our counter
    num = len(merge)
    #add the new data to our scatterplot
    ax4[n].scatter(merge['INSTEP O3'], merge['Pandora {} NO2'.format(measTyp)],c=colors[n], s=25)

    #Add text in different colors
    ax4[n].text(0.85, 0.6, 'n = {}'.format(num), fontsize=12, color='black', transform=ax4[n].transAxes)

    #Adding a title to fig4
    ax4[n].set_title('{}'.format(locations[n]), y=.78, weight = 'bold')  # Adjust the vertical position (0 to 1)
    #Add a 1:1 line
    ax4[n].plot([min(merge['INSTEP O3']), max(merge['INSTEP O3'])], [min(merge['Pandora {} NO2'.format(measTyp)]), max(merge['Pandora {} NO2'.format(measTyp)])], color='black', linestyle='--', label='1:1 Line')

#Increase vertical space between subplots
plt.subplots_adjust(hspace=0.5)  # You can adjust the value as needed
#Single y-axis label for all subplots
fig4.text(0.03, 0.5, 'Pandora {} NO2 ({})'.format(measTyp,unit), va='center', rotation='vertical')

#Common x-axis label for all subplots
fig4.text(0.5, 0.09, 'INSTEP {} O3 (ppb)'.format(measTyp), ha='center')


#Display the plot
plt.show()

#save to a different folder so we don't confuse the script on the next iteration
Spath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\Pandora Comparisons\\'
#Create the full path with the figure name
if IQR == 'yes':
    savePath = os.path.join(Spath,'Pandora_INSTEP_scatter_NO2O3_{}_IQR'.format(measTyp))
else:
    savePath = os.path.join(Spath,'Pandora_INSTEP_scatter_NO2O3_{}'.format(measTyp))
#Save the figure to a filepath
fig4.savefig(savePath)