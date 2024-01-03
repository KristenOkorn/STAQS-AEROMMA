# -*- coding: utf-8 -*-
"""
Created on Mon Nov 27 10:34:18 2023
SURFACE DATA
Includes additional column data for troubleshooting & ppb conversions
Version edited for 2023
HCHO - 5 locations (no SJSU)
NO2 - all 6 locations
@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import os
from datetime import datetime, timedelta

#loop through locations & pollutants
locations = ['AFRC','Ames','Richmond','TMF','Whittier','SJSU']
pollutants = 'NO2'

#load in the Pandora data
#create a directory path for us to pull from / save to
path = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
 
for k in range(len(locations)):
    for n in range(len(pollutants)):

            filename = 'Pandora_{}_{}.txt'.format(locations[k],pollutants)
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
                desired_cols = [0, 18, 24, 19, 39]
                #datetime, NO2, quality_flag, surf_uncertainty, temp

            else:
                if pollutants == 'NO2':
                    desired_cols = [0, 56, 39, 57, 15, 64, 65, 68] + list(range(69, len(data.columns)))
                    #datetime, no2, quality_flag, surf_uncert, temp, max_horiz_tropo, max_vert_tropo, top_height, layer1+

                elif pollutants == 'HCHO':
                    desired_cols = [0, 45, 39, 57, 15, 64, 65, 68] + list(range(69, len(data.columns)))
                    #datetime, hcho, quality_flag, surf_uncert, temp, max_horiz_tropo, max_vert_tropo, top_height, layer1+
                    
                #make a list to hold the layer data names
                layers = []
                #get names for the layer columns
                for x in range(69, len(data.columns)):
                    layers.append(f'layer_col{x}')
                    
            #Only keep the datetime & surface concentration columns
            data = data.iloc[:, desired_cols]
            
            #Rename the remaining columns
            if locations[k] == 'SJSU':
                data.columns = ['datetime','{}'.format(pollutants),'quality_flag','surface_uncertainty','temperature']
            else:
                data.columns = ['datetime','{}'.format(pollutants),'quality_flag','surface_uncertainty','temperature','max_horiz_tropo','max_vert_tropo','top_height'] + layers

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
            savePath = os.path.join(path,'{}_surface_extra_{}.csv'.format(locations[k],pollutants))
            data.to_csv(savePath)
