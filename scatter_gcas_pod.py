# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 06:37:58 2023

Scatter the GCAS and INSTEP data all on one plot
Color = day
Marker = location

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
locations = ['AFRC','TMF','Caltech','Whittier','Redlands']
pods = ['YPODR9','YPODA2','YPODG5','YPODA7','YPODL5']
shapes = ['o','v','s','p','D']

#initialize figure (will add to on each loop)
fig4 = plt.figure(4)
ax4 = plt.axes()

#initialize our counter for how many samples we have
num = 0

for n in range(len(locations)):
    #-------------------------------------
    #first load in the gcas csv's
    gcasPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\GCAS NO2 Outputs'
    #get the filename for gcas
    gcasfilename = "GCAS_NO2_{}.csv".format(locations[n])
    #join the path and filename
    gcasfilepath = os.path.join(gcasPath, gcasfilename)
    gcas = pd.read_csv(gcasfilepath,index_col=0)
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    gcas.index = pd.to_datetime(gcas.index.values.astype('datetime64[s]'),format="%Y-%m-%d %H:%M:%S",errors='coerce')
    #rename index to datetime
    gcas = gcas.rename_axis('datetime')
    #resample to minutely - since pod data will be minutely
    gcas = gcas.resample('T').mean()
    #Change the pollutant column name
    gcas.columns.values[0] = 'GCAS NO2'
    #-------------------------------------
    #now load in the matching pod data - O3
    podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Ozone'
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
    #-------------------------------------
    #merge our dataframes
    merge = pd.merge(gcas,pod,left_index=True, right_index=True)
    #remove missing values for ease of plotting
    merge = merge.dropna()
    
    #only continue if merge isn't 0
    if merge.size != 0:
        #add a date column to help with plotting
        merge['date'] = merge.index.date
        #Create a dictionary to map datetime.date to color strings
        date_mapping = {pd.Timestamp('2023-08-22').date(): 'b',
                pd.Timestamp('2023-08-23').date(): 'r',
                pd.Timestamp('2023-08-25').date(): 'g',
                pd.Timestamp('2023-08-26').date(): 'c'}
        #Replace datetime.date with strings
        merge['date'].replace(date_mapping, inplace=True)
        
        #add the num of measurements to our counter
        num = num + len(merge)
        #-------------------------------------
        #add the new data to our scatterplot
        ax4.scatter(merge['INSTEP O3'], merge['GCAS NO2'],c=merge['date'], marker=shapes[n], s=25, label = '{}'.format(locations[n]))

#Final touches for plotting
fig4.tight_layout()  
#Add x and y axis labels
ax4.set_xlabel('INSTEP Surface O3 (ppb)')
ax4.set_ylabel('GCAS Column NO2 (molec/cm2)')

#Add text in different colors
ax4.text(0.57,0.93, '2023-08-22', fontsize=12, transform=ax4.transAxes, color='b')
ax4.text(0.57,0.88, '2023-08-23', fontsize=12, color='r', transform=ax4.transAxes)
ax4.text(0.57, 0.83, '2023-08-25', fontsize=12, color='g', transform=ax4.transAxes)
ax4.text(0.57, 0.78, '2023-08-26', fontsize=12, color='c', transform=ax4.transAxes)
ax4.text(0.57, 0.73, 'n = {}'.format(num), fontsize=12, color='black', transform=ax4.transAxes)


#Adding a title to fig4
fig4.suptitle('GCAS NO2 vs. INSTEP O3', y=1)  # Adjust the vertical position (0 to 1)
#Add a 1:1 line
plt.plot([min(merge['INSTEP O3']), max(merge['INSTEP O3'])], [min(merge['GCAS NO2']), max(merge['GCAS NO2'])], color='black', linestyle='--', label='1:1 Line')
#Create a custom legend with black and white symbols
legend_elements = [Line2D([0], [0], marker=shapes[n], color='w', markerfacecolor='k', markersize=8, label=locations[n]) for n in range(len(shapes))]
#add a legend
ax4.legend(handles=legend_elements,loc='upper right')
#Display the plot
plt.show()

#save to a different folder so we don't confuse the script on the next iteration
Spath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\GCAS NO2 Outputs\\'
#Create the full path with the figure name
savePath = os.path.join(Spath,'GCAS_INSTEP_scatter')
# Save the figure to a filepath
fig4.savefig(savePath)
