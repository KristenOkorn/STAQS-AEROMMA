# -*- coding: utf-8 -*-
"""
Applying the combined CO + CA model out to individual pods

Created on Mon Jan 22 12:21:07 2024

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import seaborn as sns
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import BaggingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from joblib import dump, load
from scipy.stats import zscore

#list of pollutants to model
pollutants = ['O3']

#list of location ranges
state = ['CA','CO']

#was bagging used?
bagging = 'no'

#list of pods to model
CAlocations = ['AFRC','TMF','Whittier','Ames','Richmond','SJSU']
CApods = ['YPODR9','YPODA2','YPODA7','YPODL6','YPODL1','YPODL9']

COlocations = ['BAO','NREL','Platteville']
COpods = ['YPODD8','YPODF1','YPODF9']

#create a directory path for us to pull from / save to
CApath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Modeling Surface Concentrations'
COpath = 'C:\\Users\\okorn\\Documents\\FRAPPE (2024 Modeling)'

for n in range(len(pollutants)):
    #get the model subfolder
    if bagging == 'yes':    
        mpath = 'Outputs_allCOCA_{}_bag_rf'.format(pollutants[n])
    else:
        mpath = 'Outputs_allCOCA_{}_rf'.format(pollutants[n])
    #load the model in
    modelName = 'allCACO_rfmodel_{}.joblib'.format(pollutants[n])
    #combine path and filename
    modelPath = os.path.join(mpath, modelName)
    #load the model
    model = load(modelPath)
        
    #create a list to store the stats for each model
    stats_list = []
        
    #-------------------------------------
    #now location loop to load the CA application data
    for k in range(len(CAlocations)):
        #load the Pandora (ML input) data
        filename = "{}_column_extra_{}.csv".format(CAlocations[k],pollutants[n])
        #combine the file and the path
        filepath = os.path.join(CApath, filename)
        ann_inputs = pd.read_csv(filepath,index_col=1)
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        ann_inputs.index = pd.to_datetime(ann_inputs.index)
        #resample to minutely - since pod data will be minutely
        ann_inputs = ann_inputs.resample('T').mean()
        #Filter so that the lowest quality data is NOT included
        ann_inputs = ann_inputs.loc[ann_inputs['quality_flag'] != 12]
        
        #for SJSU, need to add extra columns & get them in order
        if CAlocations[k] == 'SJSU':
            ann_inputs = ann_inputs[['SZA','pressure','O3','O3 AMF']]
            #now add a dummy column for TEff & atmos variability
            ann_inputs['TEff'] = 4
            ann_inputs['Atmos Variability'] = 3
            #Define the desired order of columns
            desired_order = ['SZA', 'pressure', 'O3', 'TEff', 'O3 AMF', 'Atmos Variability']
            #re-order the columns
            ann_inputs = ann_inputs[desired_order]
            
        #get rid of any unnecessary columns - will vary by pollutant
        if pollutants[n] == 'HCHO':
            ann_inputs = ann_inputs[['{}'.format(pollutants[n]),'temperature','pressure','SZA']]
        elif pollutants[n] == 'O3':
            ann_inputs = ann_inputs[['SZA','pressure','O3','TEff','O3 AMF','Atmos Variability']]

        #-------------------------------------
        #now load the matching pod data
        filename = "{}_{}.csv".format(CApods[k],pollutants[n])
        #combine the file and the path
        filepath = os.path.join(CApath, filename)
        pod = pd.read_csv(filepath,index_col=0)  
        # Convert Index to DatetimeIndex
        pod.index = pd.to_datetime(pod.index, format="%d-%b-%Y %H:%M:%S")
        #Convert the modified index to a DatetimeIndex and set the nanosecond values to zero
        pod.index = pd.to_datetime(pod.index.values.astype('datetime64[s]'), errors='coerce')
       
        #-------------------------------------
        #combine our datasets - both already in local time
        x=pd.merge(ann_inputs,pod,left_index=True,right_index=True)
        #remove NaNs
        x = x.dropna()
            
        #Remove whitespace from column labels
        x.columns = x.columns.str.strip()
        #-------------------------------------

        #now for reformatting - get our 'y' data alone
        y = pd.DataFrame(x.pop('Y_hatfield'))
   
        #-------------------------------------
        #apply the model
        y_hat = model.predict(x)
        
        #generate statistics
        r2 = r2_score(y['Y_hatfield'], y_hat)
        rmse = np.sqrt(mean_squared_error(y['Y_hatfield'], y_hat))
        mbe = np.mean(y_hat - y['Y_hatfield'])
        #store our results in a dictionary
        stats = {'AppLoc': '{}'.format(CAlocations[k]), 'R2': r2, 'RMSE': rmse, 'MBE': mbe}
        #append these to the main list
        stats_list.append(stats)
        
    #-------------------------------------
    #now load in the CO data
    for j in range(len(COlocations)):
        #load the ML input data
        filename = "{}_Pandora_extra_{}.csv".format(COlocations[j],pollutants[n])
        #combine the file and the path
        filepath = os.path.join(COpath, filename)
        ann_inputs = pd.read_csv(filepath,index_col=0)
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        ann_inputs.index = pd.to_datetime(ann_inputs.index.values.astype('datetime64[s]'),format="%Y-%m-%d %H:%M:%S", errors='coerce')
    
        #-------------------------------------
        #load the matching pod data
        filename = "{}_{}.csv".format(COpods[j],pollutants[n])
        #combine the file and the path
        filepath = os.path.join(COpath, filename)
        pod = pd.read_csv(filepath,index_col=0)  
        # Convert Index to DatetimeIndex
        pod.index = pd.to_datetime(pod.index, format="%d-%b-%Y %H:%M:%S")
        #Convert the modified index to a DatetimeIndex and set the nanosecond values to zero
        pod.index = pd.to_datetime(pod.index.values.astype('datetime64[s]'), errors='coerce')
        #Rename the pollutant column to separate it from the Pandora data
        pod.rename(columns={'O3': 'Y_hatfield'}, inplace=True)

        #combine our datasets - both already in local time
        xCO=pd.merge(ann_inputs,pod,left_index=True,right_index=True)
        
        #Remove whitespace from column labels
        xCO.columns = xCO.columns.str.strip()
        
        #Reformat to get the same columns as CA data
        xCO.rename(columns={'AMF': 'O3 AMF','Temp-Eff':'TEff'}, inplace=True)
        xCO['SZA'] = 1
        xCO['pressure'] = 2
        xCO['Atmos Variability'] = 3

        #now for reformatting - get our 'y' data alone
        y = pd.DataFrame(xCO.pop('Y_hatfield'))
        
        #Define the desired order of columns
        desired_order = ['SZA', 'pressure', 'O3', 'TEff', 'O3 AMF', 'Atmos Variability']

        #re-order the columns
        xCO = xCO[desired_order]
   
        #-------------------------------------
        #apply the model
        y_hat = model.predict(xCO)
        
        #generate statistics
        r2 = r2_score(y['Y_hatfield'], y_hat)
        rmse = np.sqrt(mean_squared_error(y['Y_hatfield'], y_hat))
        mbe = np.mean(y_hat - y['Y_hatfield'])
        #store our results in a dictionary
        statsCO = {'AppLoc': '{}'.format(COlocations[j]), 'R2': r2, 'RMSE': rmse, 'MBE': mbe}
        #append these to the main list
        stats_list.append(statsCO)
        
    #save our results to file
    savePath = os.path.join(mpath,'allCOCA_stats_application_{}.csv'.format(pollutants[n]))
    #Convert the list to a DataFrame
    stats_list = pd.DataFrame(stats_list)
    stats_list.to_csv(savePath)