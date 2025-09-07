# -*- coding: utf-8 -*-
"""
Created on Mon Oct  2 10:11:14 
@author: okorn

Make ICARRT files for INSTEP data during STAQS flight campaign

******NEED TO ADD IN -999 FOR MISSING VALUES******
header lines to edit: 115, 123, 130, 132, 138
"""

#import libraries
import pandas as pd
import numpy as np
import os
from datetime import datetime

#revision date (today's date)
r_year = '2025'
r_month = '9'
r_day = '5'

#create a directory path for us to pull from / save to
path = 'C:\\Users\\kokorn\\Documents\\2023 Deployment\\R1 STAQS Field\\'

#initialize loops
locations = ['AFRC','TMF','Whittier','Caltech','Redlands']
pods = ['YPODR9','YPODA2','YPODA7','YPODG5','YPODL5']
latitudes = [34.95991,34.38189,33.97676,34.13685,34.05985]
longitudes = [-117.88107,-117.67809,-118.03032,-118.12608,-117.14573]
pollutants = ['CH4','HCHO','O3','CO2']

for k in range(len(pods)):
    #Initialize the file
    output_name = 'staqs-{}-CH4-CH2O-O3-CO2_INSTEP_20230607_R1.ict'.format(locations[k])
    
    #-------------------------------------
    #load in the data for each pollutant
    for n in range(len(pollutants)):
        filename = "{}_{}_field_corrected.csv".format(pods[k],pollutants[n])
        #read in the first worksheet from the workbook myexcel.xlsx
        filepath = os.path.join(path, filename)
        pod = pd.read_csv(filepath,index_col=0)  
        #remove any negatives
        pod = pod[pod.iloc[:, 0] >= 0]
        #Rename the index to match that of the pandora
        pod = pod.rename_axis('datetime')
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        pod.index = pd.to_datetime(pod.index,errors='coerce')
        #Change the pollutant column name
        pod.columns.values[0] = '{}'.format(pollutants[n])
        
        #if this is the first pollutant, initialize our data storage
        if n == 0:
            data = pod
        #else, merge this with the previous data
        else:
            data = pd.merge(data,pod,left_index=True, right_index=True, how='outer')
        #-------------------------------------

    #make sure our time column was imported as a datetime (w fractional seconds)
    data.index = pd.to_datetime(data.index,infer_datetime_format=True)
    
    #need to make sure each pod is in UTC
    if locations[k] != 'Redlands':
        data.index = data.index + pd.DateOffset(hours=7)
    
    #need to fill missing values with -999
    #create a blank dataframe with all minutely values included
    min_time = data.index.min() #get the range of values to include
    max_time = data.index.max() #get the range of values to include
    complete_time_range = pd.date_range(start=min_time, end=max_time, freq='1min')
    time_df = pd.DataFrame({'datetime' : complete_time_range})
    time_df.set_index('datetime', inplace=True) #set the datetime column as the index
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    time_df.index = pd.to_datetime(time_df.index,format="%d-%b-%Y %H:%M:%S",errors='coerce')
    
    #now merge our blank dataframe with the original
    data = pd.merge(time_df, data,left_index=True, right_index=True, how='outer')
    data['HCHO'].fillna(-9999.00, inplace=True)
    data['O3'].fillna(-9999.00,inplace=True)
    data['CH4'].fillna(-9999.00, inplace=True)
    data['CO2'].fillna(-9999.00, inplace=True)
    
    #add the latitude and longitude columns
    data['Latitude'] = None
    data['Longitude'] = None
    
    data['Latitude'] = data['Latitude'].fillna(latitudes[k])
    data['Longitude'] = data['Longitude'].fillna(longitudes[k])
    
    #create DataFrame with desired variables
    #initialize new time variables here
    #convert O3 to ppb here as well
    df = pd.DataFrame({'Time_Start': data.index,
            'Time_Stop':np.empty((len(data.index),), dtype=datetime),
            'Time_Mid':np.empty((len(data.index),), dtype=datetime),
            'CH4' : data['CH4'],
            'CH2O': data['HCHO'],
            'O3': data['O3'],
            'CO2': data['CO2'],
            'Latitude' : data['Latitude'],
            'Longitude' : data['Longitude']})

    #make sure our time columns were imported as datetimes (w fractional seconds) (again)
    df['Time_Start']= pd.to_datetime(df['Time_Start'],format='%m/%d/%Y %H:%M:%S')
    df['Time_Stop']= pd.to_datetime(df['Time_Stop'],format='%m/%d/%Y %H:%M:%S')
    df['Time_Mid']= pd.to_datetime(df['Time_Mid'],format='%m/%d/%Y %H:%M:%S')
    
    #reset the index to make it start at 0
    df = df.reset_index(drop=True)

    #now populate time_mid and time_end
    df[df.columns[1]] = df.iloc[:, 0] + pd.Timedelta(seconds=59)
    df[df.columns[2]] = df.iloc[:, 0] + pd.Timedelta(seconds=30)
  
    #make sure our datetimes are all in ascending order        
    df = df.sort_values(by='Time_Start')  

    #reset the index to get rid of 0's where we added times in
    df = df.reset_index(drop=True)
    
    # %% output data
         
    #convert timestamp to seconds after midnight on 6/7/2023
    #Set the reference datetime
    reference_datetime = pd.to_datetime('6/7/2023 00:00:00', format='%m/%d/%Y %H:%M:%S')
    #Calculate the time difference in seconds
    df['Time_Start'] = (df['Time_Start'] - reference_datetime).dt.total_seconds()
    df['Time_Stop'] = (df['Time_Stop'] - reference_datetime).dt.total_seconds()
    df['Time_Mid'] = (df['Time_Mid'] - reference_datetime).dt.total_seconds()
    
    #loop that saves string formatted (commas, decimal places) data
    #create new file; overwrites if needed
    with open(output_name,"w") as ofile:
        fmt = '%.0f, %.0f, %.0f, %.2f, %.2f, %.2f, %.2f, %f, %f'
        np.savetxt(ofile, df.values, fmt=fmt)

    #create file header
    #--------------------------------------------------------
    #refer to ICARTT 2.0 specifications for more details
    header = '40,1001,V02_2016\n' # number of lines in header, file format index
    header += 'Okorn, Kristen\n' # PI name
    header += 'NASA Ames Research Center\n' # PI affiliation
    header += 'INSTEP Low-Cost Sensors\n' # data source description
    header += 'STAQS 2023\n' # mission name
    header += '1,1\n' # file volume number, total number of file volumes
    header += '2023,06,07, {}, {}, {}\n'.format(r_year,r_month,r_day) # date of data collection, date of most recent revision
    header += '0\n' # data interval code
    header += 'Time_Start, seconds past midnight UTC 2023/06/07, elapsed time from 0000 UTC   \n' # name of independent variable, units of variable
    header += '8\n' # number of dependent variables
    header += '1,1,1,1,1,1,1,1\n' # scale factors of dependent variables
    header += '-9999.00,-9999.00,-9999.00,-9999.00,-9999.00,-9999.00,-9999.00,-9999.00\n' # missing data flags of dependent variables
    header += 'Time_Stop, seconds past midnight UTC 2023/06/07, Time Stop\n' # dependent variable short name, units, standard name
    header += 'Time_Mid, seconds past midnight UTC 2023/06/07, Time Midpoint\n' # dependent variable short name, units, standard name
    header += 'CH4, ppmv, Gas_CH4_InSitu_None\n' # dependent variable short name, units, standard name
    header += 'CH2O, ppbv, Gas_CH2O_InSitu_None\n' # dependent variable short name, units, standard name
    header += 'O3, ppbv, Gas_O3_InSitu_None\n' # (repeat as necessary)
    header += 'CO2, ppmv, Gas_CO2_InSitu_None\n' # (repeat as necessary)
    header += 'Latitude, degrees, Met_latitude_InSitu_None\n' # dependent variable short name, units, standard name
    header += 'Longitude, Degs, Met_longitude_InSitu_None\n' # (repeat as necessary)
    header += '0\n' # number of special comment lines (not including this line)
    header += '18\n' # number of normal comment lines (not including this line)
    header += 'PI_CONTACT_INFO: Kristen.E.Okorn@nasa.gov\n'
    header += 'PLATFORM: Ground-based at tripod or rooftop height\n'
    header += 'LOCATION: {} - also see latitude and longitude columns\n'.format(locations[k])
    header += 'ASSOCIATED_DATA: N/A\n'
    header += 'INSTRUMENT_INFO: Low-cost ground-based sensor packages; see website for additional details: https://www.nasa.gov/inexpensive-network-sensor-technology-exploring-pollution-instep/.\n'
    header += 'DATA_INFO: Low-cost sensor data subject to additional calibrations in future release\n'
    header += 'UNCERTAINTY: Uncertainty varies slightly for each sensor package. Median uncertainty for full calibration data is approximately: 23% for CH4, 40% for CH2O, 10% for O3, and 13% for CO2. Contact PI for more information.\n'
    header += 'ULOD_FLAG: -7777\n'
    header += 'ULOD_VALUE: N/A\n'
    header += 'LLOD_FLAG: -8888\n'
    header += 'LLOD_VALUE: N/A\n'
    header += 'DM_CONTACT_INFO: Kristen Okorn (Kristen.E.Okorn@nasa.gov)\n'
    header += 'PROJECT_INFO: NASA Ames Trace Gas Data (2023 STAQS)\n'
    header += 'STIPULATIONS_ON_USE: This data is subject to further review. Users must consult the PI and/or DM prior to use. As a matter of professional courtesy, consideration for co-authorship is expected for publications utilizing this data.\n'
    header += 'OTHER_COMMENTS: N/A\n'
    header += 'REVISION: R1\n'
    header += 'R1: Field data. Previous revisions may contain significant overfitting.\n'
    header += 'Time_Start,Time_Stop,Time_Mid,CH4,CH2O,O3,CO2,Latitude,Longitude\n'

    #append the defined header to the already created data file
    with open(output_name, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(header + content)      
