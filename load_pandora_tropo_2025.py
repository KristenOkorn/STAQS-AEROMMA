# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
"""
Created on Tue Nov 28 16:38:54 2023

Edited to extract tropo column data - not surface

Includes additional columns with relevant info - flags, height, temp etc.

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import os

#loop through locations & pollutants
locations = ['Ames','Richmond','CSUS','TMF','AFRC','Whittier','Bayonne','Bristol','Bronx','CapeElizabeth','Cornwall','EastProvidence','Londonderry','Lynn','MadisonCT','ManhattanNY','NewBrunswick','NewHaven','OldField','Philadelphia','Pittsburgh','Queens','WashingtonDC','Westport']
pollutant = 'HCHO'

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
            
            #get the correct columns
            if pollutant == 'NO2':
                desired_cols = [0,  #datetime
                                61, #NO2 tropospheric column
                                38, #quality_flag
                                62, #independent uncertainty
                                14, #temperature
                                64, #max_vert_tropo
                                67, #top_height
                                13, #pressure
                                3]  #SZA
                                #+ list(range(69, len(data.columns))) #layer1+

            elif pollutant == 'HCHO':
                desired_cols = [0, #datetime
                                48, #HCHO tropospheric column
                                49, #independent uncertainty
                                38, #L2 data quality flag (0=high)
                                14, #temperature
                                51, #max vert tropo
                                52, #top height
                                13, #pressure
                                3] #SZA
                                #+ list(range(55, len(data.columns))) #layer1+
                    
                #make a list to hold the layer data names
                #layers = []
                #get names for the layer columns
                #for x in range(55, len(data.columns)):
                    #layers.append(f'layer_col{x}')
                    
            #Only keep the datetime & surface concentration columns
            data = data.iloc[:, desired_cols]

            #Rename the remaining columns
            data.columns = ['datetime',
                            '{}'.format(pollutant),
                            'independent_uncertainty',
                            'quality_flag',
                            'temperature',
                            'max_vert_tropo',
                            'top_height',
                            'pressure',
                            'SZA'] 
                            #+ layers

            #Remove the 'T' and 'Z' characters from the DateColumn
            data['datetime'] = data['datetime'].str.replace('T', '').str.replace('Z', '')
            
            #Convert the DateColumn to datetime
            data['datetime'] = pd.to_datetime(data['datetime'], format='%Y%m%d%H%M%S.%f')

            #Round the fractional seconds to whole seconds
            data['datetime'] = data['datetime'].dt.round('S')
     
            #save out the final data
            savePath = os.path.join(path,'{}_tropo_extra_{}.csv'.format(locations[k],pollutant))
            data.to_csv(savePath)
