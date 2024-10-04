# -*- coding: utf-8 -*-
"""
Created on Thu Sep 22 22:54:39 2022
Edited Fri Oct 4 2024 for Aeromma

@author: okorn

Load in TCCON data
"""

#Import helpful toolboxes etc.
import pandas as pd
import os
import netCDF4 as nc
from scipy.io import netcdf
import numpy as np
from  datetime import datetime, timedelta

#create a directory path for us to pull from / save to
path = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\TCCON\\'

#locations to loop through
location = ['AFRC','Caltech']

#loop through each file to load in

for i in range(len(location)):

    #get the filename to be loaded
    filename = "{}_TCCON.NC".format(location[i])
    #combine the paths with the filenames for each
    filepath = os.path.join(path, filename)

    #load in the file
    temp = nc.Dataset(filepath)

    #get the time array and unmask it
    time = np.array(temp.variables['time'][:])
    #convert from seconds to datetime
    time = [(datetime(1970,1,1) + timedelta(seconds = td)) for td in time]

    #get the desired variables - CO2, CH4, CO
    CH4 = np.array(temp.variables['xch4'][:])
    CO = np.array(temp.variables['xco'][:])
    CO2 = np.array(temp.variables['xco2'][:])

    #turn this into a dictionary, then a dataframe
    data = {'time': time,'CH4': CH4,'CO': CO,'CO2': CO2}
    df = pd.DataFrame(data)
    
    #Rename time to datetime
    df.rename(columns={'time': 'datetime'}, inplace=True)
    #Set the 'time' column as index if it's not already a datetime index
    df = df.set_index('datetime')
    #keep only the aeromma dates of interest - jun-aug2023
    df = df[(df.index >= pd.Timestamp('2023-06-01 00:00:00')) & (df.index <= pd.Timestamp('2023-08-31 23:59:59'))]
    
    #save out the final data
    savePath = os.path.join(path,'{}_TCCON.csv'.format(location[i]))
    df.to_csv(savePath)

