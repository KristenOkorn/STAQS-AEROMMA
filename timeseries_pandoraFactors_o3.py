# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 08:41:11 2024

Timeseries pod & Pandora-derived surface estimate
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

#factor - which input we are plotting
factors = ['SZA','pressure','O3','TEff','O3 AMF']
#and give descriptors / y-axis labels for each
factor_labels = ['Solar Zenith Angle (deg)', 'Pressure (mbar)', 'O3 Total Column (mol/m2)','O3 Effective Temperature (K)', 'Direct O3 Air Mass Factor', 'Atmospheric Variability (%)']

#pollutant
pollutants = ['O3']
#datatype will vary based on pollutant
dtype = ['column','tropo']

#tt = ['train','test']

for n in range(len(pollutants)):
    for i in range(len(factors)):
        
        #initialize figure
        fig4, ax4 = plt.subplots(len(locations), 1, figsize=(8, 4 * len(locations)))

        for k in range(len(locations)):
            #-------------------------------------
            #load in the model data
            path = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Modeling Surface Concentrations'
            #load the Pandora (ML input) data
            filename = "{}_{}_extra_{}.csv".format(locations[k],dtype[n],pollutants[n])
            #combine the file and the path
            filepath = os.path.join(path, filename)
            ann_inputs = pd.read_csv(filepath,index_col=1)
            #Convert the index to a DatetimeIndex and set the nanosecond values to zero
            ann_inputs.index = pd.to_datetime(ann_inputs.index)
            #resample to minutely - since pod data will be minutely
            ann_inputs = ann_inputs.resample('T').mean()
            #Filter so that the lowest quality data is NOT included
            ann_inputs = ann_inputs.loc[ann_inputs['quality_flag'] != 12]
            #Filter to only include data during our 6 months of interest
            ann_inputs = ann_inputs[(ann_inputs.index >= '2023-06-01') & (ann_inputs.index <= '2023-12-31')]
        
            #-------------------------------------
            #add the data to our scatterplot
            ax4[k].scatter(ann_inputs.index, ann_inputs['{}'.format(factors[i])],c=colors[k], s=25)

            #Add text in different colors
            ax4[k].text(0.05, 0.8, 'R2 train = {}'.format(r2_train[n]), fontsize=12, color=colors[n], transform=ax4[n].transAxes)
            ax4[k].text(0.05, 0.6, 'R2 test = {}'.format(r2_test[n]), fontsize=12, color='black', transform=ax4[n].transAxes)

            #Adding a title to fig4
            ax4[k].set_title('{}'.format(locations[k]), y=.78, weight='bold')  # Adjust the vertical position (0 to 1)
    
        #Increase vertical space between subplots
        plt.subplots_adjust(hspace=0.2)  # You can adjust the value as needed
        #Single y-axis label for all subplots
        fig4.text(0.03, 0.5, '{}'.format(factor_labels[i]), va='center', rotation='vertical')

        #Display the plot
        plt.show()

        #save to a different folder so we don't confuse the script on the next iteration
        Spath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Modeling Surface Concentrations\\Modeling Surface O3 Plots'
        #Create the full path with the figure name
        savePath = os.path.join(Spath,'{}_{}_timeseries_2023.png'.format(factors[i],pollutants[n]))
        #Save the figure to a filepath
        fig4.savefig(savePath)