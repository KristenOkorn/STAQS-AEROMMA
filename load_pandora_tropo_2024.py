# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
"""
Created on Tue Nov 28 16:38:54 2023

Edited to extract tropo column data - not just surface

Includes additional columns with relevant info - flags, height, temp etc.

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import os
from datetime import datetime, timedelta

#loop through locations & pollutants
locations = ['AFRC','Ames','Richmond','TMF','Whittier']
pollutant = 'NO2'

#load in the Pandora data
#create a directory path for us to pull from / save to
path = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
 
for k in range(len(locations)):
    for n in range(len(pollutant)):

            filename = 'Pandora_{}_{}.txt'.format(locations[k],pollutant)
            filepath = os.path.join(path, filename)
            
            #----Remove the headers----
            #Define the target text string
            target_string = "---------------------------------------------------------------------------------------"
            #Open the text file for reading
            with open(filepath, "r") as file:
                #Initialize a counter to keep track of how many times the target string has been encountered
                target_count = 0

                #Iterate through the lines of the file along with their line numbers
                for line_number, line in enumerate(file, start=1):
                    #Check if the line contains the target string
                    if target_string in line:
                        #Increment the counter
                        target_count += 1

                        #Check if we have encountered the target string twice
                        if target_count == 2:
                            break  #Exit the loop and start processing the rest of the file
            
            #----Now read in line by line----
            # Initialize a list to store the data rows
            data_rows = []
            #Open the text file for reading
            with open(filepath, "r") as file:
                for i, line in enumerate(file, start=1):
                    if i <= line_number:
                        continue  # Skip the specified line
                    columns = line.strip().split(' ')
                    data_rows.append(columns)
            #Create a DataFrame from the list of data rows
            data = pd.DataFrame(data_rows)
            
            #get the correct columns - different for SJSU (NO2 only)
            if locations[k] == 'SJSU':
                desired_cols = [0, 19, 20, 23, 38]
                #datetime, NO2,tropo_uncert, quality flag, temp
                #all -1 from how they're listed in data key - zero indexing

            else:
                if pollutant == 'NO2':
                    layer = 68 #get the index that the layers start at
                    desired_cols = [0, 14, 38, 61, 62, 64, 67] + list(range(layer, len(data.columns)))
                    #datetime, temp, quality_flag, no2 tropo, tropo_uncert, max_vert_tropo, top_height, layer1+

                elif pollutant == 'HCHO':
                    layer = 53 #get the index that the layers start at
                    desired_cols = [0, 14, 38, 48, 49, 51, 52] + list(range(layer, len(data.columns)))
                    #datetime, temp, quality_flag, hcho, tropo_uncert, max_vert_tropo, top_height, layer1+
                    
                #make a list to hold the layer data names
                layers = []
                #get names for the layer columns
                for x in range(layer, len(data.columns)):
                    layers.append(f'layer_col{x}')
                    
            #Only keep the datetime & surface concentration columns
            data = data.iloc[:, desired_cols]

            #Rename the remaining columns
            if locations[k] == 'SJSU':
                data.columns = ['datetime','{}'.format(pollutant),'uncertainty','temperaure']
            else:
                data.columns = ['datetime','temperature', 'quality_flag','{}'.format(pollutant),'uncertainty','max_vert_tropo','top_height'] + layers

            #Remove the 'T' and 'Z' characters from the DateColumn
            data['datetime'] = data['datetime'].str.replace('T', '').str.replace('Z', '')
            
            if locations[k] == 'SJSU':
                #Convert the DateColumn to datetime - different format for SJSU
                data['datetime'] = pd.to_datetime(data['datetime'], format='%Y%m%d%H%M%S.%f', errors='coerce')
                
            else:
                #Convert the DateColumn to datetime
                data['datetime'] = pd.to_datetime(data['datetime'], format='%Y%m%d%H%M%S.%f')

            #Round the fractional seconds to whole seconds
            data['datetime'] = data['datetime'].dt.round('S')
     
            #save out the final data
            savePath = os.path.join(path,'{}_tropo_extra_{}.csv'.format(locations[k],pollutant))
            data.to_csv(savePath)
