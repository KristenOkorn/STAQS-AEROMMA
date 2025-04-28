# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 10:42:56 2025

Plot Picarro data on the same axes as INSTEP

Does CH4 and CO2 in the same script

Also does TCCON in the same script

HALO is a different aircraft so no overlap with DC-8 - make separate HALO plots

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import math

#get the relevant location data for each
locations = ['Whittier','Redlands','Caltech','TMF'] #'AFRC', 'TMF',
pods = ['YPODA7','YPODL5','YPODG5','YPODA2'] #'YPODR9', 'YPODA2',

for n in range(len(locations)): 
    #-------------------------------------
    #load in the PICARRO data
    if locations[n] == 'Whittier' or locations[n] == 'Redlands' or locations[n] == 'Caltech':
        picarroPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\Picarro CO2 CH4 CO\\'
        #get the filename for the pod
        picarrofilename = "Picarro_CH4_CO2_{}.csv".format(locations[n])
        #read in the first worksheet from the workbook myexcel.xlsx
        picarrofilepath = os.path.join(picarroPath, picarrofilename)
        picarro = pd.read_csv(picarrofilepath,index_col=0)  
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        picarro.index = pd.to_datetime(picarro.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
       
        #convert altitude - file is off by a factor of 10
        picarro['altitude'] = picarro['altitude']/10
        
        #split into separate co2 & ch4 files - helpful for handling missing data
        picarroch4 = picarro
        picarroco2 = picarro
        
        #remove any negatives (again) for CO2
        picarroch4 = picarroch4[picarroch4['CH4_ppb'] >= 0]
        picarroco2 = picarroco2[picarroco2['CO2_ppm'] >= 0]
        
        #Convert ppb to ppm for CH4
        picarroch4['CH4_ppm'] = picarroch4['CH4_ppb']/1000
    
    #-------------------------------------
    #now load in the matching pod data - CH4
    podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\RB STAQS Field 2024'
    #get the filename for the pod
    podfilename = "{}_CH4.csv".format(pods[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    podfilepath = os.path.join(podPath, podfilename)
    podch4 = pd.read_csv(podfilepath,index_col=0)  
    #remove any negatives
    podch4 = podch4[podch4.iloc[:, 0] >= 0]
    #Rename the index to match that of the pandora
    podch4 = podch4.rename_axis('datetime')
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    podch4.index = pd.to_datetime(podch4.index,format="%d-%b-%Y %H:%M:%S",errors='coerce')
    #Change the pollutant column name
    podch4.columns.values[0] = 'INSTEP CH4'
    #add a column for altitude - will all be 0
    podch4['INSTEP altitude'] = 0
    
    #get the data into UTC (from PDT) #different for each pod!!
    if locations[n] != 'Redlands':
        podch4.index += pd.to_timedelta(7, unit='h')
    
    #-------------------------------------
    #now load in the matching pod data - CO2
    #get the filename for the pod
    podfilename = "{}_CO2.csv".format(pods[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    podfilepath = os.path.join(podPath, podfilename)
    podco2 = pd.read_csv(podfilepath,index_col=0)  
    #remove any negatives
    podco2 = podco2[podco2.iloc[:, 0] >= 0]
    #Rename the index to match that of the pandora
    podco2 = podco2.rename_axis('datetime')
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    podco2.index = pd.to_datetime(podco2.index,format="%d-%b-%Y %H:%M:%S",errors='coerce')
    #Change the pollutant column name
    podco2.columns.values[0] = 'INSTEP CO2'
    #add a column for altitude - will all be 0
    podco2['INSTEP altitude'] = 0
    
    #get the data into UTC (from PDT) #different for each pod!!
    if locations[n] != 'Redlands':
        podco2.index += pd.to_timedelta(7, unit='h')

    #-------------------------------------
    
    #now load in the matching TCCON data - Caltech & AFRC only
    if locations[n] == 'Caltech' or locations[n] == 'AFRC':
        tcconPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\TCCON'
        #get the filename for the tccon data
        tcconfilename = "{}_TCCON.csv".format(locations[n])
        #read in the first worksheet from the workbook myexcel.xlsx
        tcconfilepath = os.path.join(tcconPath, tcconfilename)
        tccon = pd.read_csv(tcconfilepath,index_col=0)  
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        tccon.index = pd.to_datetime(tccon.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
        #resample to minutely
        tccon = tccon.resample('T').median()
        #Change the pollutant column name
        tccon.rename(columns={'CH4':'TCCON CH4', 'CO2':'TCCON CO2'}, inplace=True)
    
        #-------------------------------------
        #we only need to merge the tccon data with our CH4 & CO2
        
        #get a minute avg for picarro so we don't have to match s or ms
        picarroch4_minutely = picarroch4.resample('1T').mean()
        picarroco2_minutely = picarroco2.resample('1T').mean()
        #now get all of the times to match - both picarro & pod
        picarroch4_pod_agg = picarroch4_minutely.index.union(podch4.index)
        picarroco2_pod_agg = picarroco2_minutely.index.union(podco2.index)
        #now filter tccon based on these  aggregates
        tcconch4 = tccon[tccon.index.isin(picarroch4_pod_agg)]
        tcconco2 = tccon[tccon.index.isin(picarroco2_pod_agg)]
        
        #and drop missing values
        tcconch4 = tcconch4.dropna()
        tcconco2 = tcconco2.dropna()
    
    #-------------------------------------    
    #Get global min/max to standardize x & y axes
    x_max_ch4 = math.ceil(max(picarroch4['CH4_ppm'].max(), podch4['INSTEP CH4'].max()))
    x_min_ch4 = math.ceil(min(picarroch4['CH4_ppm'].min(), podch4['INSTEP CH4'].min())) -0.15
    y_max_ch4 = picarro['altitude'].max() +80

    #and repeat for co2
    x_max_co2 = math.ceil(max(picarroco2['CO2_ppm'].max(), podco2['INSTEP CO2'].max()))
    x_min_co2 = math.ceil(min(picarroco2['CO2_ppm'].min(), podco2['INSTEP CO2'].min())) -10
    y_max_co2 = math.ceil(picarro['altitude'].max() +80)
    
    #overwrite y_max if whittier - one high point messing up the scale
    if locations[n] == 'Whittier':
        y_max_ch4 = math.ceil(picarro.loc[picarro['altitude'] < 5000, 'altitude'].max() + 80)
        y_max_co2 = math.ceil(picarro.loc[picarro['altitude'] < 5000, 'altitude'].max() + 80)
        
        
    #and use 0 for y's, but with cushion to keep edge values in plotting
    y_min = -10
    
    #-------------------------------------
    #figure out how many days we have - for how many subplots
    #in general, we have more ch4 than co2, so use ch4
    num_unique_days = len(np.unique(picarro.index.date))
    #also get the list of them to split by
    unique_days_list = np.unique(picarro.index.date).tolist()
    
    # Create a dictionary to store DataFrames for each unique day
    ch4_split_dataframes = {}
    co2_split_dataframes = {}
    picarroch4_split_dataframes = {}
    picarroco2_split_dataframes = {}
    tcconch4_split_dataframes = {}
    tcconco2_split_dataframes = {}

    #Split the DataFrame based on unique days
    for day in unique_days_list:
        #get for the picarro ch4
        picarroch4_day_data = picarroch4[picarroch4.index.date == day]
        picarroch4_split_dataframes[day] = picarroch4_day_data
        #and repeat for the picarro co2
        picarroco2_day_data = picarroco2[picarroco2.index.date == day]
        picarroco2_split_dataframes[day] = picarroco2_day_data
        #and repeat for pod ch4
        ch4_day_data = podch4[podch4.index.date == day]
        ch4_split_dataframes[day] = ch4_day_data
        #and repeat for pod co2
        co2_day_data = podco2[podco2.index.date == day]
        co2_split_dataframes[day] = co2_day_data
        if locations[n] == 'Caltech' or locations[n] == 'AFRC':
            #and repeat for tccon ch4
            tcconch4_day_data = tcconch4[tcconch4.index.date == day]
            tcconch4_split_dataframes[day] = tcconch4_day_data
            #and repeat for tccon co2
            tcconco2_day_data = tcconco2[tcconco2.index.date == day]
            tcconco2_split_dataframes[day] = tcconco2_day_data
    
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(num_unique_days, 2, figsize=(16, 4 * num_unique_days))
    
    # If there is only one subplot, make it a list to handle indexing
    if num_unique_days == 1:
        axs = [axs]

    #first plot the flight data for ch4
    for k, (day, df) in enumerate(picarroch4_split_dataframes.items()):
        #CH4 in the right column
        axs[k,1].scatter(df['CH4_ppm'], df['altitude'], label='Picarro', color='black')
        
    #and repeat with the flight data for co2
    for k, (day, df) in enumerate(picarroco2_split_dataframes.items()):
        #CO2 in the left column
        axs[k,0].scatter(df['CO2_ppm'], df['altitude'], label='Picarro', color='black')
        
    #add the tccon ch4 data if applicable
    if locations[n] == 'Caltech' or locations[n] == 'AFRC':
        for k, (day, df) in enumerate(tcconch4_split_dataframes.items()): 
            #use our max y's to create an altitude column for tccon if applicable
            if locations[n] == 'Caltech' or locations[n] == 'AFRC':
                #get the altitude for ch4
                df['altitude'] = np.linspace(0, y_max_ch4, len(df))
                #now median
                df['TCCON CH4'] = np.nanmedian(df['TCCON CH4'])
                #CH4 in the right column
                #and create a linspace of only 15 points so its not too crowded on the plot
                lin_ch4 = df.iloc[np.linspace(0, len(df) - 1, 15, dtype=int)]['TCCON CH4']
                lin_alt = df.iloc[np.linspace(0, len(df) - 1, 15, dtype=int)]['altitude']
                axs[k,1].scatter(lin_ch4, lin_alt, label='TCCON', color='purple')
        
        #add the tccon co2 data if applicable
        for k, (day, df) in enumerate(tcconco2_split_dataframes.items()):
            if locations[n] == 'Caltech' or locations[n] == 'AFRC':
                #get the altitude column for co2
                df['altitude'] = np.linspace(0, y_max_co2, len(df))
                #now median
                df['TCCON CO2'] = np.nanmedian(df['TCCON CO2'])
                #CO2 in the left column
                #and create a linspace of only 15 points so its not too crowded on the plot
                lin_co2 = df.iloc[np.linspace(0, len(df) - 1, 15, dtype=int)]['TCCON CO2']
                lin_alt = df.iloc[np.linspace(0, len(df) - 1, 15, dtype=int)]['altitude']
                axs[k,0].scatter(lin_ch4, lin_alt, label='TCCON', color='purple')
        
    #then plot the pod ch4 & do some formatting
    for k, (day, df) in enumerate(ch4_split_dataframes.items()):   
        axs[k,1].scatter(df['INSTEP CH4'], df['INSTEP altitude'], label='INSTEP', color='red')
        #Add a title with the date to each subplot
        axs[k,1].set_title('{}'.format(day), y=.9)  # Adjust the vertical position (0 to 1)
        axs[k,1].legend(loc='upper right', bbox_to_anchor=(1.0, 0.9))
        # Set the font size of the tick labels
        axs[k,1].tick_params(axis='both', labelsize=12)
        
        #Standardize the axes
        axs[k,1].set_xlim(x_min_ch4, x_max_ch4)
        axs[k,1].set_ylim(y_min, y_max_ch4)
        axs[k,1].autoscale(False)
    
    #then plot the pod co2 & do some formatting
    for k, (day, df) in enumerate(co2_split_dataframes.items()):
        axs[k,0].scatter(df['INSTEP CO2'], df['INSTEP altitude'], label='INSTEP', color='red')
        #Add a title with the date to each subplot
        axs[k,0].set_title('{}'.format(day), y=.9)  # Adjust the vertical position (0 to 1)
        axs[k,0].legend(loc='upper right', bbox_to_anchor=(1.0, 0.9))
        # Set the font size of the tick labels
        axs[k,0].tick_params(axis='both', labelsize=12)
        
        #Standardize the axes
        axs[k,0].set_xlim(x_min_co2, x_max_co2)
        axs[k,0].set_ylim(y_min, y_max_ch4)
        axs[k,0].autoscale(False)
        
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.2, top=0.9, bottom=0.05)  # You can adjust the value as needed
    #Single y-axis label for all subplots
    fig.text(0.03, 0.5, 'Altitude (m)', va='center', rotation='vertical',fontsize=16)
    #Common x-axis label for all subplots in each column
    axs[-1,1].set_xlabel('CH4(ppm)', ha='center',fontsize=16)
    axs[-1,0].set_xlabel('CO2(ppm)', ha='center',fontsize=16)
    
    #Add an overall title to the plot
    fig.text(0.5,0.91,'{}'.format(locations[n]), ha = 'center', fontsize=16, weight = 'bold')

    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\Picarro Plots\\'
    
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'altitude_CH4_CO2_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)
