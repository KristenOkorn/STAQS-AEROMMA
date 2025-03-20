# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 09:28:40 2025
Altitude plot of DC-8, Pandora, & pod
Updated Pandora conversion info
For Pandora: use filter for same window instead of merge for exact alignment
Also leave out the limiting one (filter should work for this too)

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from datetime import timedelta

#get the relevant location data for each
locations = ['TMF','Whittier','Caltech','Redlands','AFRC']
pods = ['YPODA2','YPODA7','YPODG5','YPODL5','YPODR9']
#locations = ['St Anthony','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park'] #'AFRC'
#pods = ['St Anthony','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park'] #'YPODR9'

#pollutant?
pollutant = 'HCHO'

#use interquartile range for Pandora instead of full range?
IQR = 'no'

for n in range(len(locations)): 
    #-------------------------------------
    #load in the in-situ data - ISAF HCHO
    isafPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\ISAF Outputs\\'
    #get the filename for the pod
    isaffilename = "ISAF_HCHO_{}.csv".format(locations[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    isaffilepath = os.path.join(isafPath, isaffilename)
    isaf = pd.read_csv(isaffilepath,index_col=0)  
    #remove any negatives
    isaf = isaf[isaf.iloc[:, 0] >= 0]
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    isaf.index = pd.to_datetime(isaf.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
    #convert ppt to ppb
    isaf[' CH2O_ISAF'] = isaf[' CH2O_ISAF']/1000
    #convert altitude - file is off by a factor of 10
    isaf['altitude'] = isaf['altitude']/10
    #-------------------------------------
    #next load in the pandora tropo csv's - skip for sites without one
    if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
        pandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
        #get the filename for pandora
        pandorafilename = "{}_tropo_extra_HCHO.csv".format(locations[n])
        #join the path and filename
        pandorafilepath = os.path.join(pandoraPath, pandorafilename)
        pandora = pd.read_csv(pandorafilepath,index_col=1)
        #Reset the seconds to zero in the index
        pandora.index = pandora.index.str.replace(r'\d{2}$', '00')
        #Convert the index to a DatetimeIndex
        pandora.index = pd.to_datetime(pandora.index)#rename index to datetime
        pandora = pandora.rename_axis('datetime')
        #Filter so the lowest quality flag is omitted
        pandora = pandora.loc[pandora['quality_flag'] != 12]
        #get rid of any unnecessary columns
        pandora = pandora[['HCHO','temperature','top_height','max_vert_tropo']]
        #resample to minutely - since pod data will be minutely
        #pandora = pandora.resample('T').mean()
        #Change the pollutant column name
        pandora.columns.values[0] = 'Pandora Tropo HCHO'
        #remove any negatives
        pandora = pandora[pandora.iloc[:, 0] >= 0]
        #convert from mol/m2 to ppb
        pandora['Pandora Tropo HCHO'] = pandora['Pandora Tropo HCHO']*0.08206*pandora['temperature']*1000/(pandora['max_vert_tropo'])
        #-------------------------------------

        surfpandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
        #get the filename for pandora
        surfpandorafilename = "{}_surface_extra_HCHO.csv".format(locations[n])
        #join the path and filename
        surfpandorafilepath = os.path.join(surfpandoraPath, surfpandorafilename)
        surfpandora = pd.read_csv(surfpandorafilepath,index_col=1)
        #Reset the seconds to zero in the index
        surfpandora.index = surfpandora.index.str.replace(r'\d{2}$', '00')
        #Convert the index to a DatetimeIndex
        surfpandora.index = pd.to_datetime(surfpandora.index)#rename index to datetime
        surfpandora = surfpandora.rename_axis('datetime')
        #Filter to only use high quality data
        surfpandora = surfpandora.loc[surfpandora['quality_flag'] != 12]
        #hold onto the HCHO data and relevant parameters only
        surfpandora = surfpandora[['HCHO','temperature','top_height','max_vert_tropo']]
        #resample to minutely - since pod data will be minutely
        #surfpandora = surfpandora.resample('T').mean()
        #Change the pollutant column name
        surfpandora.columns.values[0] = 'Pandora Surface HCHO'
        #remove any negatives
        surfpandora = surfpandora[surfpandora.iloc[:, 0] >= 0]
        #convert mol/m3 to ppb
        surfpandora['Pandora Surface HCHO'] = surfpandora['Pandora Surface HCHO']*0.08206*surfpandora['temperature']*(10**(9))/1000
        #add a column for altitude - will all be 0
        surfpandora['Surface Pandora altitude'] = 0
    #-------------------------------------
    #now load in the matching pod data - HCHO
    if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] =='Redlands' or locations[n] == 'Caltech' or locations[n] == 'AFRC':
        #podPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\Field Data'
        podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\RB STAQS Field 2024'
        #get the filename for the pod
        podfilename = "{}_HCHO.csv".format(pods[n])
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
        pod.columns.values[0] = 'INSTEP HCHO'
        #add a column for altitude - will all be 0
        pod['INSTEP altitude'] = 0
        
        #need to get in UTC time to match the DC-8 & Pandora
        #L5 & L9 already good, convert the rest
        if pods[n] != 'YPODL5' or pods[n] != 'YPODL9':
            pod.index = pod.index + timedelta(hours = 7)
    
    #-------------------------------------
    #now load in the matching SCAQMD data - HCHO
    if locations[n] != 'TMF' and locations[n] != 'Whittier' and locations[n] !='Redlands' and locations[n] != 'Caltech' and locations[n] != 'AFRC':
        #podPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\Field Data'
        scaqmdPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\SCAQMD Data'
        #get the filename for the pod
        scaqmdfilename = "{}.csv".format(pods[n])
        #read in the first worksheet from the workbook myexcel.xlsx
        scaqmdfilepath = os.path.join(scaqmdPath, scaqmdfilename)
        scaqmd = pd.read_csv(scaqmdfilepath,index_col=0)  
        # Replace '--' with NaN in values column
        scaqmd['HCHO'] = scaqmd['HCHO'].replace('--', np.nan)
        #Convert values from string to float
        scaqmd['HCHO'] = scaqmd['HCHO'].astype(float)
        #remove any negatives
        scaqmd = scaqmd[scaqmd.iloc[:, 0] >= 0]
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        scaqmd.index = pd.to_datetime(scaqmd.index,errors='coerce')
        #Change the pollutant column name
        scaqmd.columns.values[0] = 'SCAQMD HCHO'
        #add a column for altitude - will all be 0
        scaqmd['SCAQMD altitude'] = 0
    
        #get the data into UTC (from PDT)
        scaqmd.index += pd.to_timedelta(7, unit='h')
    #-------------------------------------
    #merge our dataframes
    if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] =='Redlands' or locations[n] == 'Caltech' or locations[n] == 'AFRC':
        #For pod locations
        merge = pd.merge(isaf,pod,left_index=True, right_index=True)
    else:
        #For SCAQMD locations
        merge = pd.merge(isaf,scaqmd,left_index=True, right_index=True)
    #filter to match times for pandora also - except for caltech & redlands
    if locations[n] == 'Whittier' or locations[n] == 'TMF' or locations[n] == 'AFRC':
        #get the start and end times from the merge file
        start_time = merge.index[0]
        end_time = merge.index[-1]
        #now filter based on this
        pandora = pandora[(pandora.index >= start_time) & (pandora.index <= end_time)]
        surfpandora = surfpandora[(surfpandora.index >= start_time) & (surfpandora.index <= end_time)]
     
        if IQR == 'yes':
            # Calculate the interquartile range (IQR) for the tropo pandora
            q1 = pandora['Pandora Tropo {}'.format(pollutant)].quantile(0.25)
            q3 = pandora['Pandora Tropo {}'.format(pollutant)].quantile(0.75)
            iqr = q3 - q1
        
            #Set the y-limits based on the IQR
            x_min = q1 - 1.5 * iqr
            x_max = q3 + 1.5 * iqr
        
            #filter the dataframe based on the IQR
            pandora = pandora[(pandora['Pandora Tropo {}'.format(pollutant)] >= x_min) & (pandora['Pandora Tropo {}'.format(pollutant)] <= x_max)]
            
            #-------------------------------------------------------------
            # Calculate the interquartile range (IQR) for the surface pandora
            q1 = surfpandora['Pandora Surface {}'.format(pollutant)].quantile(0.25)
            q3 = surfpandora['Pandora Surface {}'.format(pollutant)].quantile(0.75)
            iqr = q3 - q1
        
            #Set the y-limits based on the IQR
            x_min = q1 - 1.5 * iqr
            x_max = q3 + 1.5 * iqr
        
            #filter the dataframe based on the IQR
            surfpandora = surfpandora[(surfpandora['Pandora Surface {}'.format(pollutant)] >= x_min) & (surfpandora['Pandora Surface {}'.format(pollutant)] <= x_max)]
    
    #remove missing values for ease of plotting
    merge = merge.dropna()
    if locations[n] == 'Whittier' or locations[n] == 'TMF' or locations[n] == 'AFRC':
        pandora = pandora.dropna()
        surfpandora = surfpandora.dropna()
    
    #-------------------------------------
    #figure out how many days we have - for how many subplots
    num_unique_days = len(np.unique(merge.index.date))
    #also get the list of them to split by
    unique_days_list = np.unique(merge.index.date).tolist()
    
    # Create a dictionary to store DataFrames for each unique day
    split_dataframes = {}
    if locations[n] == 'Whittier' or locations[n] == 'TMF' or locations[n] == 'AFRC':
        pandora_split_dataframes = {}
        surfpandora_split_dataframes = {}

    #Split the DataFrame based on unique days
    for day in unique_days_list:
        day_data = merge[merge.index.date == day]
        split_dataframes[day] = day_data
        #now repeat for the pandora data
        if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
            pandora_day_data = pandora[pandora.index.date == day]
            pandora_split_dataframes[day] = pandora_day_data
            #now repeat for the surface pandora data
            surfpandora_day_data = surfpandora[surfpandora.index.date == day]
            surfpandora_split_dataframes[day] = surfpandora_day_data
            
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(num_unique_days, 1, figsize=(8, 4 * num_unique_days))
    
    # If there is only one subplot, make it a list to handle indexing
    if num_unique_days == 1:
        axs = [axs]

    for k, (day, df) in enumerate(split_dataframes.items()):
        if locations[n] == 'Whittier' or locations[n] == 'TMF' or locations[n] == 'AFRC':
            #create a regular set of y's (altitude) for the Pandora tropo data
            if len(pandora_day_data) <10:
                #Create empty rows at the end to populate
                empty_rows = pd.DataFrame(np.nan, index=range(10-len(pandora_day_data)), columns=pandora_split_dataframes[day].columns)
                #Append the empty rows to the DataFrame
                pandora_day_data = pd.concat([pandora_day_data, empty_rows], ignore_index=True)
                #then proceed to fill them
                pandora_day_data['Pandora_alt'] = np.linspace(0, max(df['altitude']), len(pandora_day_data))
            else: #proceed as normal if we have enough points
                pandora_day_data['Pandora_alt'] = np.linspace(0, max(df['altitude']), len(pandora_day_data))
            #also add a set of y's at 0 for the surface pandora estimatea
            surfpandora_day_data['Pandora_alt'] = np.linspace(0, 0, len(surfpandora_day_data))
            
        #first plot the flight data
        axs[k].scatter(df[' CH2O_ISAF'], df['altitude'], label='ISAF', color='black')
        #then plot the instep data
        if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] =='Redlands' or locations[n] == 'Caltech' or locations[n] == 'AFRC':
            axs[k].scatter(df['INSTEP HCHO'], df['INSTEP altitude'], label='INSTEP', color='red')
        else:
            axs[k].scatter(df['SCAQMD HCHO'], df['SCAQMD altitude'], label='SCAQMD', color='red')
        
        #then plot the pandora data, if there is any
        if locations[n] == 'TMF' or locations[n] == 'Whittier' or locations[n] == 'AFRC':
            #replace the tropo data with the median before plotting
            pandora_day_data['Pandora Tropo HCHO'] = np.nanmedian(pandora_day_data['Pandora Tropo HCHO'])
            axs[k].scatter(pandora_day_data['Pandora Tropo HCHO'], pandora_day_data['Pandora_alt'], label='Pandora Tropospheric Column', color='blue')
            axs[k].scatter(surfpandora_day_data['Pandora Surface HCHO'], surfpandora_day_data['Pandora_alt'], label='Pandora Surface Estimate', color='green')
        
        #Add a title with the date to each subplot
        axs[k].set_title('{}'.format(day), y=.9)  # Adjust the vertical position (0 to 1)
        axs[k].legend(loc='upper right', bbox_to_anchor=(1.0, 0.9))
        
        # Set the font size of the tick labels
        axs[k].tick_params(axis='both', labelsize=12)
        
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.2, top=0.9, bottom=0.05)  # You can adjust the value as needed
    #Single y-axis label for all subplots
    fig.text(0.03, 0.5, 'Altitude (m)', va='center', rotation='vertical',fontsize=16)
    #Common x-axis label for all subplots
    #fig.text(0.5, 0.1, 'HCHO (ppb)', ha='center',fontsize=16)
    axs[-1].set_xlabel('HCHO (ppb)', ha='center',fontsize=16)
    #Add an overall title to the plot
    fig.text(0.5,0.91,'{}'.format(locations[n]), ha = 'center', fontsize=16, weight = 'bold')

    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\ISAF HCHO Plots\\'
    #Create the full path with the figure name
    if IQR == 'yes':
        savePath = os.path.join(Spath,'altitude_HCHO_{}_IQR'.format(locations[n]))
    else:
        savePath = os.path.join(Spath,'altitude_HCHO_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)
