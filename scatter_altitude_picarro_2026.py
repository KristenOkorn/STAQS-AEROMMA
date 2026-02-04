# -*- coding: utf-8 -*-
"""
Created on Fri Jan 30 14:54:19 2026

Plot Picarro data altitude plot - timing fixes for 2026

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import math
from datetime import datetime, timedelta

#get the relevant location data for each
locations = ['Whittier','Redlands','TMF','AFRC', 'Caltech']
pods = ['YPODA7','YPODL5','YPODA2','YPODR9', 'YPODG5']

#define threshold for gaps in data to be counted as separate flights
#most flights are about 5hrs long
gap_threshold = pd.Timedelta(hours=2)

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
        
        #time difference between consecutive rows
        dt = picarroch4.index.to_series().diff()
        #new flight whenever the threshold gap is exceeded (not midnight bc crossover UTC issues)
        new_coin = (dt.isna()) | (dt >= gap_threshold)
        #flight counter (global)
        coin_id = new_coin.cumsum() -1
        #add to the isaf df
        picarroch4["coincidence"] = coin_id.astype(int)
        #get the start & end and pad +/- 1hr on each side 
        pad = pd.Timedelta(hours=1)
        #make sure the count is numeric
        picarroch4["coincidence"] = pd.to_numeric(picarroch4["coincidence"])
        #now create coincidence window with pad (-1 to zero index)
        ch4_coin_windows = {coin : (grp.index.min() - pad, grp.index.max() + pad) for coin, grp in picarroch4.groupby("coincidence")}
        
        #do the same for co2
        #time difference between consecutive rows
        dt = picarroch4.index.to_series().diff()
        #new flight whenever the threshold gap is exceeded (not midnight bc crossover UTC issues)
        new_coin = (dt.isna()) | (dt >= gap_threshold)
        #flight counter (global)
        coin_id = new_coin.cumsum() -1
        #add to the isaf df
        picarroco2["coincidence"] = coin_id.astype(int)
        #get the start & end and pad +/- 1hr on each side 
        pad = pd.Timedelta(hours=1)
        #make sure the count is numeric
        picarroco2["coincidence"] = pd.to_numeric(picarroco2["coincidence"])
        #now create coincidence window with pad (-1 to zero index)
        co2_coin_windows = {coin : (grp.index.min() - pad, grp.index.max() + pad) for coin, grp in picarroco2.groupby("coincidence")}
        
        #Set up min/maxes for later
        ch4_max = max(picarroch4['CH4_ppm'])
        ch4_alt_max = max((picarroch4['altitude']) + 80)
        co2_max = max(picarroco2['CO2_ppm'])
        co2_alt_max = max((picarroco2['altitude']) + 80)
        #and use 0 for all mins - 80s are so points don't get cut off at the edges
        x_min = 0
        y_min = -80
    
    #-------------------------------------
    #now load in the matching pod data - CH4
    podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\R1 STAQS Field'
    #get the filename for the pod
    podfilename = "{}_CH4_field_corrected.csv".format(pods[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    podfilepath = os.path.join(podPath, podfilename)
    podch4 = pd.read_csv(podfilepath,index_col=0)  
    #remove any negatives
    podch4 = podch4[podch4.iloc[:, 0] >= 0]
    #Rename the index to match that of the pandora
    podch4 = podch4.rename_axis('datetime')
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    podch4.index = pd.to_datetime(podch4.index,errors='coerce')
    #Change the pollutant column name
    podch4.columns.values[0] = 'INSTEP CH4'
    #add a column for altitude - will all be 0
    podch4['INSTEP altitude'] = 0
    
    #now group the pod data by coincidence
    podch4["coincidence"] = pd.NA
    #add in the grouping windows
    for coin, (t0, t1) in ch4_coin_windows.items(): 
        mask = (podch4.index >= t0) & (podch4.index <= t1) 
        podch4.loc[mask, "coincidence"] = coin
    #drop rows that didn't match any window
    podch4 = podch4.dropna(subset=["coincidence"])
    
    #also get the pod max
    if podch4.empty:
        global_max = ch4_max
    else:
        podch4_max = max(podch4['INSTEP CH4'])
        #and now get the overall max
        if ch4_max > podch4_max:
            global_max = ch4_max
        else:
            global_max = podch4_max

    #-------------------------------------
    #now load in the matching pod data - CO2
    #get the filename for the pod
    podfilename = "{}_CO2_field_corrected.csv".format(pods[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    podfilepath = os.path.join(podPath, podfilename)
    podco2 = pd.read_csv(podfilepath,index_col=0)  
    #remove any negatives
    podco2 = podco2[podco2.iloc[:, 0] >= 0]
    #Rename the index to match that of the pandora
    podco2 = podco2.rename_axis('datetime')
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    podco2.index = pd.to_datetime(podco2.index,errors='coerce')
    #Change the pollutant column name
    podco2.columns.values[0] = 'INSTEP CO2'
    #add a column for altitude - will all be 0
    podco2['INSTEP altitude'] = 0
    
    #now group the pod data by coincidence
    podco2["coincidence"] = pd.NA
    #add in the grouping windows
    for coin, (t0, t1) in co2_coin_windows.items(): 
        mask = (podco2.index >= t0) & (podco2.index <= t1) 
        podco2.loc[mask, "coincidence"] = coin
    #drop rows that didn't match any window
    podco2 = podco2.dropna(subset=["coincidence"])
    
    #also get the pod max
    podco2_max = max(podco2['INSTEP CO2'])
    #and now get the overall max
    if co2_max > podco2_max:
        global_max = co2_max
    else:
        global_max = podco2_max

    #-------------------------------------
    #now load in the tardiss Co2 data - for AFRC & Caltech only
    if locations[n] == 'AFRC' or locations[n] == 'Caltech':
        #get the tardiss co2 file path
        tardiss_path = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\TARDISS\\TARDISS Outputs'
        #get the filename for the tardiss data
        tardissfilename = "{}_CO2_tardiss_lower.csv".format(locations[n])
        #read in the first worksheet from the workbook myexcel.xlsx
        tardissfilepath = os.path.join(tardiss_path, tardissfilename)
        tardiss = pd.read_csv(tardissfilepath,index_col=0)  
        #make datetime the index
        tardiss = tardiss.set_index("datetime")
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        tardiss.index = pd.to_datetime(tardiss.index,errors='coerce')
        
        #get a minute average for tardiss so we don't have to match s or ms
        tardiss = tardiss.resample('1T').mean()
        
        #now group the tardiss data by coincidence
        tardiss["coincidence"] = pd.NA
        #add in the grouping windows
        for coin, (t0, t1) in co2_coin_windows.items(): 
            mask = (tardiss.index >= t0) & (tardiss.index <= t1) 
            tardiss.loc[mask, "coincidence"] = coin
        #drop rows that didn't match any window
        tardiss = tardiss.dropna(subset=["coincidence"])
    
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
        
        #split into separate CH4 & CO2 df's
        tcconch4 = tccon.drop(columns={'TCCON CO2'})
        tcconco2 = tccon.drop(columns={'TCCON CH4'})
        
        #now group the CH4 TCCON data by coincidence
        tcconch4["coincidence"] = pd.NA
        #add in the grouping windows
        for coin, (t0, t1) in ch4_coin_windows.items(): 
            mask = (tcconch4.index >= t0) & (tcconch4.index <= t1) 
            tcconch4.loc[mask, "coincidence"] = coin
        #drop rows that didn't match any window
        tcconch4 = tcconch4.dropna(subset=["coincidence"])
        
        #now group the CO2 TCCON data by coincidence
        tcconco2["coincidence"] = pd.NA
        #add in the grouping windows
        for coin, (t0, t1) in co2_coin_windows.items(): 
            mask = (tcconco2.index >= t0) & (tcconco2.index <= t1) 
            tcconco2.loc[mask, "coincidence"] = coin
        #drop rows that didn't match any window
        tcconco2 = tcconco2.dropna(subset=["coincidence"])
    
    #-------------------------------------
    #figure out how many days we have - for how many subplots
    num_coin= len(ch4_coin_windows)
    #also get the list of them to split by
    ch4_coin_list = ch4_coin_windows.keys()
    co2_coin_list = co2_coin_windows.keys()
    
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(num_coin, 2, figsize=(16, 4 * num_coin))
    
    
    # If there is only one subplot, make it a list to handle indexing
    if num_coin == 1:
        axs = [axs]
    #-------------------------------------
    
    #now start plotting ch4 - new subplot for each coincidence
    for l, coin in enumerate(ch4_coin_list):
        
        #limit  each dataframe to the current coincidence
        picarroch4_lim = picarroch4[picarroch4["coincidence"] == coin]
        podch4_lim = podch4[podch4["coincidence"] == coin]
        
        #first plot the ch4 flight data
        if not picarroch4_lim.empty:
            axs[l,1].scatter(picarroch4['CH4_ppm'], picarroch4['altitude'], label='Picarro', color='black')
        #then plot the pod ch4 data
        if not podch4_lim.empty:
            axs[l,1].scatter(podch4_lim['INSTEP CH4'], podch4_lim['INSTEP altitude'], label='INSTEP', color='magenta')
    
        #add the tccon data if applicable
        if locations[n] == 'Caltech' or locations[n] == 'AFRC':
            #limit  each dataframe to the current coincidence
            tcconch4_lim = tcconch4[tcconch4["coincidence"] == coin]
            
            #start with tccon ch4
            if not tcconch4_lim.empty:
                #get the altitude for tccon ch4
                tcconch4_lim['altitude'] = np.linspace(0, ch4_alt_max, len(tcconch4_lim))
                #now median
                tcconch4_lim['TCCON CH4'] = np.nanmedian(tcconch4_lim['TCCON CH4'])
                #CH4 in the right column
                #and create a linspace of only 15 points so its not too crowded on the plot
                lin_ch4 = tcconch4_lim.iloc[np.linspace(0, len(tcconch4_lim) - 1, 15, dtype=int)]['TCCON CH4']
                lin_alt = tcconch4_lim.iloc[np.linspace(0, len(tcconch4_lim) - 1, 15, dtype=int)]['altitude']
                #now plot tccon ch4    
                axs[l,1].scatter(lin_ch4, lin_alt, label='TCCON', color='orange')
                
            
        #---Subplot Beautification---
        #Standardize the axes - ch4
        axs[l,1].set_xlim(1.75, ch4_max)
        axs[l,1].set_ylim(y_min, ch4_alt_max)
        axs[l,1].autoscale(False)
        
        #Standardize the axes - co2
        axs[l,0].set_xlim(375, co2_max)
        axs[l,0].set_ylim(y_min, co2_alt_max)
        axs[l,0].autoscale(False)
        
        #override for whittier - high points throwing off zoom
        if locations[n] == 'Whittier':
            axs[l,1].set_ylim(y_min,800)
            axs[l,0].set_ylim(y_min,800)
            
        #Now plot the legend for both
        axs[l,1].legend(loc='upper right', bbox_to_anchor=(1.0, 0.7)) 
        axs[l,0].legend(loc='upper right', bbox_to_anchor=(1.0, 0.7)) 
            
        #Add a subtitle with the location & coincidence to each subplot
        axs[l,1].set_title('{} - Coincidence {}'.format(locations[n],l), y=.9)  # Adjust the vertical position (0 to 1)
        axs[l,0].set_title('{} - Coincidence {}'.format(locations[n],l), y=.9)
        
        #nov25 version - individual x&y axis labels for each subplot
        axs[l,1].set_ylabel('Altitude (m)')
        axs[l,0].set_ylabel('Altitude (m)')
        axs[-1,1].set_xlabel('CH4(ppm)', ha='center',fontsize=16)
        axs[-1,0].set_xlabel('CO2(ppm)', ha='center',fontsize=16)
            
        #-------------------------------------
    #now plot all the co2 data - new subplot for each coincidence
    for l, coin in enumerate(co2_coin_list):
        
        #limit  each dataframe to the current coincidence
        picarroco2_lim = picarroco2[picarroco2["coincidence"] == coin]
        podco2_lim = podco2[podco2["coincidence"] == coin]
        
        #then plot the co2 flight data
        if not picarroco2_lim.empty:
            axs[l,0].scatter(picarroco2['CO2_ppm'], picarroco2['altitude'], label='Picarro', color='black')
        #then plot the pod co2 data
        if not podco2_lim.empty:
            axs[l,0].scatter(podco2_lim['INSTEP CO2'], podco2_lim['INSTEP altitude'], label='INSTEP', color='magenta')
            
        #add the tccon & tardiss data if applicable
        if locations[n] == 'Caltech' or locations[n] == 'AFRC':
            #limit  each dataframe to the current coincidence
            tcconco2_lim = tcconco2[tcconco2["coincidence"] == coin]
            tardiss_lim = tardiss[tardiss["coincidence"] == coin]
    
            #now tccon co2
            if not tcconco2_lim.empty:
                #get the altitude for tccon ch4
                tcconco2_lim['altitude'] = np.linspace(0, co2_alt_max, len(tcconco2_lim))
                #now median
                tcconco2_lim['TCCON CO2'] = np.nanmedian(tcconco2_lim['TCCON CO2'])
                #CH4 in the right column
                #and create a linspace of only 15 points so its not too crowded on the plot
                lin_co2 = tcconco2_lim.iloc[np.linspace(0, len(tcconco2_lim) - 1, 15, dtype=int)]['TCCON CO2']
                lin_alt = tcconco2_lim.iloc[np.linspace(0, len(tcconco2_lim) - 1, 15, dtype=int)]['altitude']
                #now plot tccon ch4    
                axs[l,0].scatter(lin_co2, lin_alt, label='TCCON', color='orange')
                
            #now tardiss co2
            if not tardiss_lim.empty:   
                #lower column is between surface and ~800 hPa, 1940m at sea level
                tardiss_lim['altitude'] = np.linspace(0, 1940, len(tardiss_lim))
                #now median
                tardiss_lim['TARDISS_ppm'] = np.nanmedian(tardiss_lim['TARDISS_ppm'])
                #and create a linspace of only 8 points so its not too crowded on the plot
                lin_tardiss = tardiss_lim.iloc[np.linspace(0, len(tardiss_lim) - 1, 8, dtype=int)]['TARDISS_ppm']
                lin_alt = tardiss_lim.iloc[np.linspace(0, len(tardiss_lim) - 1, 8, dtype=int)]['altitude']
                #now plot 
                axs[l,0].scatter(lin_tardiss, lin_alt, label='TARDISS', color='purple')       
        
       
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.2, top=0.9, bottom=0.05)  # You can adjust the value as needed
    #Add an overall title to the plot
    fig.text(0.5,0.91,'{}'.format(locations[n]), ha = 'center', fontsize=16, weight = 'bold')

    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\Picarro Plots\\'
    
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'altitude_CH4_CO2_{}_newcoincidences_2hr'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)