# -*- coding: utf-8 -*-
"""
Created on Tues Jan 09 17:13:08 2024

Updated for use with STAQS/AEROMMA data

Using random forrest
Overfitting and mostly using hour
O3 - none are using pandora, all hour
NO2 - only 1/3 using pandora as the highest factor

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
pollutants = ['O3','HCHO']
#datatype will vary based on pollutant
dtype = ['column','tropo']

#list of pods to model
locations = ['AFRC','TMF','Whittier','Ames','Richmond']
pods = ['YPODR9','YPODA2','YPODA7','YPODL6','YPODL1']

#create a directory path for us to pull from / save to
path = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Modeling Surface Concentrations'

for n in range(len(pollutants)):
    for k in range(len(locations)):
        #load the Pandora (ML input) data
        filename = "{}_{}_extra_{}.csv".format(locations[k],dtype[n],pollutants[n])
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
        #now load the matching pod data
        filename = "{}_{}.csv".format(pods[k],pollutants[n])
        #combine the file and the path
        filepath = os.path.join(path, filename)
        pod = pd.read_csv(filepath,index_col=0)  
        # Convert Index to DatetimeIndex
        pod.index = pd.to_datetime(pod.index, format="%d-%b-%Y %H:%M:%S")
        #Convert the modified index to a DatetimeIndex and set the nanosecond values to zero
        pod.index = pd.to_datetime(pod.index.values.astype('datetime64[s]'), errors='coerce')
   
        #combine our datasets - both already in local time
        x=pd.merge(ann_inputs,pod,left_index=True,right_index=True)
        #remove NaNs
        x = x.dropna()
        
        #Remove whitespace from column labels
        x.columns = x.columns.str.strip()
        
        #now for reformatting - get our 'y' data alone
        y = pd.DataFrame(x.pop('Y_hatfield'))
        
        #Now do our test-train split
        X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=.2)

        #Create a Random Forest regressor object
        rf_regressor = RandomForestRegressor()
        
        #Train the Random Forest regressor on the training data
        rf_regressor.fit(X_train, y_train)
        
        # make predictions
        y_hat_train = rf_regressor.predict(X_train)
        y_hat_test = rf_regressor.predict(X_test)
        
        #now add the predictions  & y's back to the original dataframes
        X_train['y_hat_train'] = y_hat_train
        X_test['y_hat_test'] = y_hat_test
        X_train['Y'] = y
        
        #Get the feature importances
        importances = rf_regressor.feature_importances_

        #Create a dictionary of importance labels with their corresponding input labels
        importance_labels = {label: importance for label, importance in zip(x.columns, importances)}
        
        #generate statistics for test data
        r2 = r2_score(y_test['Y_hatfield'], y_hat_test)
        rmse = np.sqrt(mean_squared_error(y_test['Y_hatfield'], y_hat_test))
        mbe = np.mean(y_hat_test - y_test['Y_hatfield'])
        #store our results in a dictionary
        stats_test = {'R2': r2, 'RMSE': rmse, 'MBE': mbe}
        
        #generate statistics for train data
        r2 = r2_score(y_train['Y_hatfield'], y_hat_train)
        rmse = np.sqrt(mean_squared_error(y_train['Y_hatfield'], y_hat_train))
        mbe = np.mean(y_hat_train - y_train['Y_hatfield'])
        #store our results in a dictionary
        stats_train = {'R2': r2, 'RMSE': rmse, 'MBE': mbe}
        
        #save all of our results to file
        
        #Name a new subfolder
        subfolder_name = 'Outputs_{}_rf'.format(pollutants[n])
        #Create the subfolder path
        subfolder_path = os.path.join(path, subfolder_name)
        #Create the subfolder
        os.makedirs(subfolder_path, exist_ok=True)

        #save out the final data
        
        #X_train
        savePath = os.path.join(subfolder_path,'{}_X_train_{}.csv'.format(locations[k],pollutants[n]))
        X_train.to_csv(savePath)
        
        #X_test
        savePath = os.path.join(subfolder_path,'{}_X_test_{}.csv'.format(locations[k],pollutants[n]))
        X_test.to_csv(savePath)
        
        #Importance labels
        savePath = os.path.join(subfolder_path,'{}_Factor_importance_{}.csv'.format(locations[k],pollutants[n]))
        # Convert the dictionary to a DataFrame
        importance_labels = pd.DataFrame.from_dict(importance_labels, orient='index', columns=['Value'])
        importance_labels.to_csv(savePath)
        
        #Stats_train
        savePath = os.path.join(subfolder_path,'{}_stats_train_{}.csv'.format(locations[k],pollutants[n]))
        # Convert the dictionary to a DataFrame
        stats_train = pd.DataFrame.from_dict(stats_train, orient='index', columns=['Value'])
        stats_train.to_csv(savePath)
        
        #Stats_test
        savePath = os.path.join(subfolder_path,'{}_stats_test_{}.csv'.format(locations[k],pollutants[n]))
        # Convert the dictionary to a DataFrame
        stats_test = pd.DataFrame.from_dict(stats_test, orient='index', columns=['Value'])
        stats_test.to_csv(savePath)
        
        #Save the rf model itself
        savePath = os.path.join(subfolder_path,'{}_rfmodel_{}.joblib'.format(locations[k],pollutants[n]))
        dump(rf_regressor, savePath)
