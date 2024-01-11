# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 17:55:55 2024

Scatter the pod & Pandora-derived surface estimate
All subplots in 1 figure

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
r2_train = ['0.982','0.994','0.998','0.995','0.985']
r2_test = ['0.893','0.963','0.987','0.966','0.860']

#pollutant
pollutant = 'O3'

tt = ['train','test']

#initialize figure
fig4, ax4 = plt.subplots(len(locations), 1, figsize=(8, 4 * len(locations)))

for n in range(len(locations)): 
    #-------------------------------------
    #load in the train & test data
    path = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Modeling Surface Concentrations\\Outputs_O3_rf'
    for k in range(len(tt)):
        #get the filename for the train data
        filename = "{}_X_{}_O3.csv".format(locations[n],tt[k])
        #join the path and filename
        filepath = os.path.join(path, filename)
        t = pd.read_csv(filepath,index_col=0)
        #Reset the seconds to zero in the index
        t.index = t.index.str.replace(r'\d{2}$', '00')
        #Convert the index to a DatetimeIndex
        t.index = pd.to_datetime(t.index)
        #rename index to datetime
        t = t.rename_axis('datetime')
        #get rid of any unnecessary columns
        if tt[k] == 'test':
            t = t[['y_hat_test']]
            #rename to make clear which is which
            test = t
            #get the number of points
            num_test = len(test)
        elif tt[k] == 'train':
            t = t[['y_hat_train']]
            #rename to make clear which is which
            train = t
            #get the number of points
            num_train = len(train)

    #-------------------------------------
    #now load in the matching pod data - O3
    podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Modeling Surface Concentrations'
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
    #merge = pd.merge(pod,test,left_index=True, right_index=True)
    #merge = pd.merge(merge,train,left_index=True, right_index=True)
    #remove missing values for ease of plotting
    #merge = merge.dropna()
    merge = pd.concat([pod,test,train], axis=1)
    
    #-------------------------------------
    #add the training data to our scatterplot
    ax4[n].scatter(merge['INSTEP O3'], merge['y_hat_test'],c='black', s=25)
    #add the testing data in black
    ax4[n].scatter(merge['INSTEP O3'], merge['y_hat_train'],c=colors[n], s=25)

    #Add text in different colors
    ax4[n].text(0.05, 0.9, 'n (train) = {}'.format(num_train), fontsize=12, color=colors[n], transform=ax4[n].transAxes)
    ax4[n].text(0.05, 0.8, 'R2 train = {}'.format(r2_train[n]), fontsize=12, color=colors[n], transform=ax4[n].transAxes)
    ax4[n].text(0.05, 0.7, 'n (test) = {}'.format(num_test), fontsize=12, color='black', transform=ax4[n].transAxes)
    ax4[n].text(0.05, 0.6, 'R2 test = {}'.format(r2_test[n]), fontsize=12, color='black', transform=ax4[n].transAxes)

    #Adding a title to fig4
    ax4[n].set_title('{}'.format(locations[n]), y=.78, weight='bold')  # Adjust the vertical position (0 to 1)
    
    #Add best fit lines for both
    #ax4[n].plot([min(merge['INSTEP O3']), max(merge['INSTEP O3'])], [min(merge['y_hat_train']), max(merge['y_hat_train'])], color=colors[n], linestyle='--')
    #ax4[n].plot([min(merge['INSTEP O3']), max(merge['INSTEP O3'])], [min(merge['y_hat_test']), max(merge['y_hat_test'])], color='black', linestyle='--')

    #Add 1-1 line
    ax4[n].plot([min(merge['INSTEP O3']), max(merge['INSTEP O3'])], [min(merge['INSTEP O3']), max(merge['INSTEP O3'])], color='black')
    
#Increase vertical space between subplots
plt.subplots_adjust(hspace=0.2)  # You can adjust the value as needed
#Single y-axis label for all subplots
fig4.text(0.03, 0.5, 'Estimated O3 (ppb)', va='center', rotation='vertical')
#Common x-axis label for all subplots
fig4.text(0.5, 0.1, 'INSTEP O3 (ppb)', ha='center')

#Display the plot
plt.show()

#save to a different folder so we don't confuse the script on the next iteration
Spath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Modeling Surface Concentrations\\Modeling Surface O3 Plots'
#Create the full path with the figure name
savePath = os.path.join(Spath,'INSTEP_estimate_scatter_O3_ttsplit.png')
#Save the figure to a filepath
fig4.savefig(savePath)