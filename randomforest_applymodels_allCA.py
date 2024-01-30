# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 18:23:35 2024

Apply the ALL CA random forest to individual Pandora sites
Seeing how transferrable the new algorithm is

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
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from joblib import dump, load

#list of pollutants to model
pollutants = ['O3']
#datatype will vary based on pollutant
dtype = ['column','tropo']

#list of pods to model
locations = ['AFRC','TMF','Whittier','Ames','Richmond']
pods = ['YPODR9','YPODA2','YPODA7','YPODL6','YPODL1']

for n in range(len(pollutants)):
        #first load the ALL CA model
        mpath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Modeling Surface Concentrations\\Outputs_{}_rf_allCA'.format(pollutants[n])
        #load the model in
        modelName = 'allCA_rfmodel_{}.joblib'.format(pollutants[n])
        #combine path and filename
        modelPath = os.path.join(mpath, modelName)
        #load the model
        model = load(modelPath)
        
        #create a list to store the stats for each model
        stats_list = []
        
        #-------------------------------------
        #now location loop to load the application data
        for j in range(len(locations)):
            #create a pandora path for us to pull from / save to
            path = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Modeling Surface Concentrations'
            #load the Pandora (ML input) data
            filename = "{}_{}_extra_{}.csv".format(locations[j],dtype[n],pollutants[n])
            #combine the file and the path
            filepath = os.path.join(path, filename)
            ann_inputs = pd.read_csv(filepath,index_col=1)
            #Convert the index to a DatetimeIndex and set the nanosecond values to zero
            ann_inputs.index = pd.to_datetime(ann_inputs.index)
            #resample to minutely - since pod data will be minutely
            ann_inputs = ann_inputs.resample('T').mean()
            #Filter so that the lowest quality data is NOT included
            ann_inputs = ann_inputs.loc[ann_inputs['quality_flag'] != 12]
            #get rid of any unnecessary columns - will vary by pollutant
            if pollutants[n] == 'HCHO':
                ann_inputs = ann_inputs[['{}'.format(pollutants[n]),'temperature','pressure','SZA']]
            elif pollutants[n] == 'O3':
                ann_inputs = ann_inputs[['SZA','pressure','O3','TEff','O3 AMF','Atmos Variability']]

            #-------------------------------------
            #now load the "ground truth" pod data
            filename = "{}_{}.csv".format(pods[j],pollutants[n])
            #combine the file and the path
            filepath = os.path.join(path, filename)
            pod = pd.read_csv(filepath,index_col=0)  
            #Convert Index to DatetimeIndex
            pod.index = pd.to_datetime(pod.index, format="%d-%b-%Y %H:%M:%S")
            #Convert the modified index to a DatetimeIndex and set the nanosecond values to zero
            pod.index = pd.to_datetime(pod.index.values.astype('datetime64[s]'), errors='coerce')
            
            #-------------------------------------
            #combine our datasets - both already in local time
            x=pd.merge(ann_inputs,pod,left_index=True,right_index=True)
            #remove NaNs
            x = x.dropna()
    
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
            stats = {'AppLoc': '{}'.format(locations[j]), 'R2': r2, 'RMSE': rmse, 'MBE': mbe}
            #append these to the main list
            stats_list.append(stats)
        
        #save our results to file
        savePath = os.path.join(mpath,'allCA_stats_application_{}.csv'.format(pollutants[n]))
        #Convert the list to a DataFrame
        stats_list = pd.DataFrame(stats_list)
        stats_list.to_csv(savePath)