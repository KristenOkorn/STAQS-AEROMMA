# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 09:36:41 2024

Runs separately for all matching surface-Pandora pairs

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
from sklearn.preprocessing import StandardScaler

#list of pollutants to model
pollutants = ['O3']

#was bagging used?
bagging = 'yes'

#list of pods to model
locations = ['Bayonne','Bristol','Bronx','CapeElizabeth','Cornwall','EastProvidence','Londonderry','Lynn','MadisonCT','NewBrunswick','NewHaven','OldField','Philadelphia','Pittsburgh','Queens','WashingtonDC','Westport','AFRC','TMF','Ames','Richmond','CSUS','NOAA','SLC','BAO','NREL','Platteville','AldineTX','LibertyTX','HoustonTX']
pods = ['EPA_Bayonne','EPA_Bristol','EPA_Bronx','EPA_CapeElizabeth','EPA_Cornwall','EPA_EastProvidence','EPA_Londonderry','EPA_Lynn','EPA_MadisonCT','EPA_NewBrunswick','EPA_NewHaven','EPA_OldField','EPA_Philadelphia','EPA_Pittsburgh','EPA_Queens','EPA_WashingtonDC','EPA_Westport','YPODR9','YPODA2','YPODL6','YPODL1','YPODL2','topaz','WBB','YPODD4','YPODF1','YPODF9','HoustonAldine','LibertySamHoustonLibrary','UHMoodyTower']

#create a directory path for us to pull from / save to
path = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Modeling Surface Concentrations\\All O3 Data Combined'

for n in range(len(pollutants)):
    #get the model subfolder
    if bagging == 'yes':    
        m = 'Outputs_{}_rf_all_bag'.format(pollutants[n])
    else:
        m = 'Outputs_{}_rf_all'.format(pollutants[n])
    #combine
    mpath = path + '\\' + m
    
    #now loop through for each location
    for i in range(len(locations)):
        #load the model in
        modelName = '{}_rfmodel_{}.joblib'.format(locations[i],pollutants[n])
        #combine path and filename
        modelPath = os.path.join(mpath, modelName)
        #load the model
        model = load(modelPath)
        
        #create a list to store the stats for each model
        stats_list = []
        
        #-------------------------------------
        #now location loop to load the CA application data
        for k in range(len(locations)):
            #load the Pandora (ML input) data
            filename = "{}_column_extra_{}.csv".format(locations[k],pollutants[n])
            #combine the file and the path
            filepath = os.path.join(path, filename)
            #different load structure for FRAPPE data
            if locations[k] == 'BAO' or locations[k] == 'NREL' or locations[k] == 'Platteville':
                ann_inputs = pd.read_csv(filepath,index_col=0)
            else:
                ann_inputs = pd.read_csv(filepath,index_col=1)
            #Convert the index to a DatetimeIndex and set the nanosecond values to zero
            ann_inputs.index = pd.to_datetime(ann_inputs.index)
            #remove any empty/placeholder times
            if locations[k] != 'BAO' and locations[k] != 'NREL' and locations[k] != 'Platteville': 
                ann_inputs = ann_inputs[ann_inputs['Atmos Variability'] != 999]
            ann_inputs = ann_inputs[ann_inputs['O3'] != -9e99]
            #resample to minutely - since pod data will be minutely
            ann_inputs = ann_inputs.resample('H').mean()
            #Filter so that the lowest quality data is NOT included
            if locations[k] != 'BAO' and locations[k] != 'NREL' and locations[k] != 'Platteville':
                ann_inputs = ann_inputs.loc[ann_inputs['quality_flag'] != 12]
            #get rid of any unnecessary columns - will vary by pollutant
            if pollutants[n] == 'HCHO':
                ann_inputs = ann_inputs[['{}'.format(pollutants[n]),'temperature','pressure','SZA']]
            elif pollutants[n] == 'O3':
                if locations[k] == 'BAO' or locations[k] == 'NREL' or locations[k] == 'Platteville':
                    #different columns for FRAPPE data
                    ann_inputs = ann_inputs.rename(columns={'Temp-Eff': 'TEff','AMF':'O3 AMF'})
                else: #others dont need this
                    ann_inputs = ann_inputs[['SZA','pressure','O3','TEff','O3 AMF','Atmos Variability']]
            
            #-------------------------------------
            #for SJSU, need to add extra columns & get them in order
            if locations[k] == 'SJSU':
                ann_inputs = ann_inputs[['SZA','pressure','O3','O3 AMF']]
                #now add a dummy column for TEff & atmos variability
                ann_inputs['TEff'] = 4
                ann_inputs['Atmos Variability'] = 3
                #Define the desired order of columns
                desired_order = ['SZA', 'pressure', 'O3', 'TEff', 'O3 AMF', 'Atmos Variability']
                #re-order the columns
                ann_inputs = ann_inputs[desired_order]
            
            #for FRAPPE pods, also need to add dummy columns
            if locations[k] == 'BAO' or locations[k] == 'NREL' or locations[k] == 'Platteville':
                ann_inputs['Atmos Variability'] = 3
                ann_inputs['O3 AMF'] = 2
                #Define the desired order of columns
                desired_order = ['SZA', 'pressure', 'O3', 'TEff', 'O3 AMF', 'Atmos Variability']
                #re-order the columns
                ann_inputs = ann_inputs[desired_order]
                #remove any nans from retime
                ann_inputs = ann_inputs.dropna()
            
            #data cleaning - remove negatives from the O3 column
            ann_inputs.loc[ann_inputs['O3'] < 0, 'O3'] = np.nan
            
            #-------------------------------------
            #now load the matching pod data
            filename = "{}_{}.csv".format(pods[k],pollutants[n])
            #combine the file and the path
            filepath = os.path.join(path, filename)
            
            if 'WBB' in pods[k]: #wbb, slc
                pod = pd.read_csv(filepath,skiprows=10,index_col=1)
                #delete the first row - holds unit info
                pod = pod.drop(pod.index[0])
            else:
                #all others take the same format
                pod = pd.read_csv(filepath,index_col=0)  
            
            #Convert Index to DatetimeIndex
            if 'YPOD' in pods[k]:
                pod.index = pd.to_datetime(pod.index, format="%d-%b-%Y %H:%M:%S")
                #Convert the modified index to a DatetimeIndex and set the nanosecond values to zero
                pod.index = pd.to_datetime(pod.index.values.astype('datetime64[s]'), errors='coerce')
                #if FRAPPE, need to change the column names
                if locations[k] == 'BAO' or locations[k] == 'NREL' or locations[k] == 'Platteville':
                    pod.rename(columns={'O3':'Y_hatfield'}, inplace=True)
            
            #if it's a non-pod, need to clean the data more
            elif 'topaz' in pods[k]: #topaz, noaa
                #need different format for non-pods
                pod.index = pd.to_datetime(pod.index, format="%Y-%m-%d %H:%M:%S")
                #Convert the modified index to a DatetimeIndex and set the nanosecond values to zero
                pod.index = pd.to_datetime(pod.index.values.astype('datetime64[s]'), errors='coerce')
                #Drop all columns except the specified one
                columns_to_drop = [col for col in pod.columns if col != 'O3_1m,ppbv']
                pod.drop(columns=columns_to_drop, inplace=True)
                #rename the main column
                pod.rename(columns={'O3_1m,ppbv':'Y_hatfield'}, inplace=True)
                #remove rows containing -999
                pod = pod[pod['Y_hatfield'] != -999]
            
            elif 'WBB' in pods[k]: #wbb, slc
                #Convert the modified index to a DatetimeIndex and set the nanosecond values to zero
                pod.index = pd.to_datetime(pod.index.values.astype('datetime64[s]'), errors='coerce')
                #Drop all columns except the specified one
                pod = pod[['ozone_concentration_set_1']]#rename the main column
                #rename the ozone column
                pod.rename(columns={'ozone_concentration_set_1':'Y_hatfield'}, inplace=True)
                #remove rows containing -999
                pod = pod[pod['Y_hatfield'] != -999]
                #make sure our o3 data is numbers, not strings
                pod['Y_hatfield'] = pod['Y_hatfield'].astype(float)
                
            
            elif 'TX' in pods[k]: #texas data
                pod.rename(columns={'O3':'Y_hatfield'}, inplace=True)
                pod.index = pd.to_datetime(pod.index, format="%Y-%m-%d %H:%M:%S")
                #Convert the modified index to a DatetimeIndex and set the nanosecond values to zero
                pod.index = pd.to_datetime(pod.index.values.astype('datetime64[s]'), errors='coerce')
                pod = pod.dropna()
                
            elif 'EPA' in pods[k]: #EPA data
                pod.rename(columns={'O3':'Y_hatfield'}, inplace=True)
                pod.index = pd.to_datetime(pod.index)
            
            #-------------------------------------
            #remove any nans before retime
            pod = pod.dropna()
            #resample to hourly - what we have for TX
            pod = pod.resample('H').mean()
            
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
            #scale our dataset
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(x)
   
            #-------------------------------------
            #apply the model
            y_hat = model.predict(X_scaled)
        
            #generate statistics
            r2 = r2_score(y['Y_hatfield'], y_hat)
            rmse = np.sqrt(mean_squared_error(y['Y_hatfield'], y_hat))
            mbe = np.mean(y_hat - y['Y_hatfield'])
            #store our results in a dictionary
            stats = {'AppLoc': '{}'.format(locations[k]), 'R2': r2, 'RMSE': rmse, 'MBE': mbe}
            #append these to the main list
            stats_list.append(stats)
        
        #save our results to file
        savePath = os.path.join(mpath,'allCOCA_stats_application_{}.csv'.format(pollutants[n]))
        #Convert the list to a DataFrame
        stats_list = pd.DataFrame(stats_list)
        stats_list.to_csv(savePath)