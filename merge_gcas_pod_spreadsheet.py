# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 08:31:33 2025

@author: okorn
Use before running TEMPO + GCAS plotting scripts
Merge the GCAS & pod/SCAQMD data to make sure we're pulling the best possible HCHO data
Also include temperature where applicable
"""
#Import helpful toolboxes etc
import pandas as pd
import os
import numpy as np
from datetime import timedelta

#----- Get set up for the ground data -----

#need to pluck out just the lat/lon pairs that are relevant to each pod location
podlocations = ['TMF','Whittier','Redlands','AFRC','Caltech']
pods = ['YPODA2','YPODA7','YPODL5','YPODR9','YPODG5']

#split into pods vs scaqmd
slocations = ['St Anthony','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park']#'AFRC','Caltech',

#combine all locations for ease of looping
all_locations = podlocations + slocations

#dates where we have data overlapping with GCAS
dates = ['2023-08-22','2023-08-23','2023-08-25','2023-08-26']
#----------------------------------------------

#create a dataframe to hold all our info

# Create a DataFrame with the names & dates ready
match = pd.DataFrame(columns=dates,index=all_locations)

#load in the pre-partitioned GCAS data

for n in range(len(all_locations)):     
    gcasPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\GCAS HCHO Outputs'
    #get the filename for the pod
    gcasfilename = "GCAS_HCHO_{}.csv".format(all_locations[n])
    #combine the path & filename
    gcasfilepath = os.path.join(gcasPath, gcasfilename)
    #read in the file
    gcas = pd.read_csv(gcasfilepath,index_col=0)  
    #Rename the index to datetime
    gcas = gcas.rename_axis('datetime')
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    gcas.index = pd.to_datetime(gcas.index,errors='coerce')
    #Change the pollutant column name
    gcas.columns.values[0] = 'GCAS HCHO'
    
    #now load in the matching pod data for INSTEP sites
    if all_locations[n] in podlocations:
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
        
        #get in the correct time zone
        #L5 & L9 already in UTC, convert the rest
        if pods[n] != 'YPODL5' or pods[n] != 'YPODL9':
            pod.index = pod.index + timedelta(hours = 7)
                            
        #merge within an hour of tolerance
        merge1 = pd.merge_asof(gcas, pod, left_index=True, right_index=True, direction='nearest', tolerance=pd.Timedelta('1H'))
        
        #now load in the temperature data - needed for conversion
        tempfilename = '{}_temp_2023.csv'.format(pods[n])
        tempfilepath = os.path.join(podPath, tempfilename)
        temp = pd.read_csv(tempfilepath,index_col=0) 
        #remove any negatives
        temp = temp[temp.iloc[:, 0] >= 0]
        #Rename the index to match that of the pandora
        temp = temp.rename_axis('datetime')
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        temp.index = pd.to_datetime(temp.index)
        #retime to get hourly measurements
        #temp = temp.resample('H').median()
        #Change the temperature column name
        #temp.columns.values[0] = 'temperature'
        
        #get in the correct time zone
        #L5 & L9 already in UTC, convert the rest
        if pods[n] != 'YPODL5' or pods[n] != 'YPODL9':
            temp.index = temp.index + timedelta(hours = 7)
                                
        #merge with the pod data
        if not merge1.empty:
            merge2 = pd.merge_asof(merge1, temp, left_index=True, right_index=True, direction='nearest', tolerance=pd.Timedelta('1H'))
                                              
            #convert the ppb value to molec/cm2 - assuming all HCHO is below 1000m
            pod_hcho = merge2['INSTEP HCHO'] * (1/merge2['temperature']) * 2000 * (6.022/0.0821) * (10**13)
            #add column back to dataframe
            merge2['HCHO_molec/cm2'] = pod_hcho
        
            #--------------------------------------------------
            #get the median on each day & save it to our 'match' dataframe
            for date in dates:
                if date in merge2.index:
                    #get the median value for each date & add it to the overall dataframe
                    match.iloc[n, match.columns.get_loc(date)] = np.nanmedian(merge2.loc[date, 'HCHO_molec/cm2'])
                else:
                    #fill with a NaN if we don't have overlap on this date
                    match.iloc[n, match.columns.get_loc(date)] = 'NaN'
                    
    #repeat this process for SCAQMD sites
    else:
        scaqmdPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\SCAQMD Data\\'
        #get the filename for the pod
        scaqmdfilename = "{} 2023-2024.csv".format(all_locations[n])
        #combine the file name & path
        scaqmdfilepath = os.path.join(scaqmdPath, scaqmdfilename)
        #get the data from file
        scaqmd = pd.read_csv(scaqmdfilepath,index_col=0)
        if all_locations[n] != 'Inner Port':
            #make sure the am/pm format is read in correctly
            scaqmd.index = pd.to_datetime(scaqmd.index, format='%m/%d/%Y %I:%M:%S %p')
        else:
            #inner port is already in 24hr time
            scaqmd.index = pd.to_datetime(scaqmd.index)
        #make sure the ppb values are interpreted as numbers
        scaqmd.iloc[:, 0] = scaqmd.iloc[:, 0].replace('--', np.nan).astype(float)
        #remove any negatives
        scaqmd = scaqmd[scaqmd.iloc[:, 0] >= 0]
        #Rename the index to match that of the pandora
        scaqmd = scaqmd.rename_axis('datetime')
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        scaqmd.index = pd.to_datetime(scaqmd.index,format="%m/%d/%Y %H:%M:%S %p",errors='coerce')
        #Change the pollutant column name
        scaqmd.columns.values[0] = 'SCAQMD HCHO'
        
        #convert from local time to UTC
        scaqmd.index = scaqmd.index + timedelta(hours = 7)
        
        #need to sort by index before merging
        scaqmd = scaqmd.sort_index()
        
        #merge with the gcas data
        merge3 = pd.merge_asof(gcas, scaqmd, left_index=True, right_index=True, direction='nearest', tolerance=pd.Timedelta('1H'))
        
        #now load in the temperature data - need to pull from WU
        scaqmdtempPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\SCAQMD Data\\'
        #get the filename for the pod
        if all_locations[n] == 'St Anthony' or all_locations[n] == 'Manhattan Beach' or all_locations[n] == 'Guenser Park' or all_locations[n] =='Elm Avenue':
            scaqmdtempfilename = "temp_hawthorne.csv"
        else:
            scaqmdtempfilename = "temp_longbeach.csv"
        #read in the first worksheet from the workbook myexcel.xlsx
        scaqmdtempfilepath = os.path.join(scaqmdtempPath, scaqmdtempfilename)
        stemp = pd.read_csv(scaqmdtempfilepath,index_col=0) 
        #remove any negatives
        stemp = stemp[stemp.iloc[:, 0] >= 0]
        #convert from F to K
        stemp['temp_K'] = ((5/9)*stemp['avg temp (f)']) + 459.67
        #Rename the index to match that of the pandora
        stemp = stemp.rename_axis('datetime')
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        stemp.index = pd.to_datetime(stemp.index,errors='coerce')
        
        #convert from local time to UTC
        stemp.index = stemp.index + timedelta(hours = 7)
        
        #merge our DAILY temperature with the scaqmd & gcas data
        merge4 = pd.merge_asof(merge3, stemp, left_index=True, right_index=True, direction='nearest', tolerance=pd.Timedelta('1D'))
        
        if not merge4.empty:                     
            #convert the ppb value to molec/cm2
            merge4['HCHO_molec/cm2'] = merge4['SCAQMD HCHO'] * (1/merge4['temp_K']) * 2000 *(6.022/0.0821) * (10**13)
        
            #replace infinities with nan
            merge4 = merge4.replace([np.inf, -np.inf], np.nan)
        
            #--------------------------------------------------
            #get the median on each day & save it to our 'match' dataframe
            for date in dates:
                if date in merge2.index:
                    #get the median value for each date & add it to the overall dataframe
                    match.iloc[n, match.columns.get_loc(date)] = np.nanmedian(merge4.loc[date, 'HCHO_molec/cm2'])
                else:
                    match.iloc[n, match.columns.get_loc(date)] = 'NaN'
                    
#Combine output filename and path
outputPath = os.path.join(gcasPath, "GCAS_pod_match.csv")
#Save to CSV
match.to_csv(outputPath, index=True) 