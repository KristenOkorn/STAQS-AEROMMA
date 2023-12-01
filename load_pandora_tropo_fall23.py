# -*- coding: utf-8 -*-
"""
Created on Tue Nov 28 16:38:54 2023

Edited to extract tropo column data - not just surface

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import os
from datetime import datetime, timedelta

#loop through locations & pollutants
locations = ['AFRC','Ames','Richmond','TMF','Whittier']
pollutant = 'HCHO'

#load in the Pandora data
#create a directory path for us to pull from / save to
path = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
 
for k in range(len(locations)):
    for n in range(len(pollutant)):

            filename = 'Pandora_{}_{}.txt'.format(locations[k],pollutant)
            filepath = os.path.join(path, filename)
            
            #get the correct column - different for SJSU (NO2 only)
            if locations[k] == 'SJSU':
                pollutant_cols = 20
            else:
                if pollutant == 'NO2':
                    pollutant_cols = 62
                elif pollutant == 'HCHO':
                    pollutant_cols = 49
            
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

            #Only keep the datetime & surface concentration columns
            data = data.iloc[:, [0,pollutant_cols]]

            #Rename the remaining columns
            data.columns = ['datetime','{}'.format(pollutant)]

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
            savePath = os.path.join(path,'{}_tropo_{}.csv'.format(locations[k],pollutant))
            data.to_csv(savePath)