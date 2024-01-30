# -*- coding: utf-8 -*-
"""
Created on Fri Jan 19 08:42:35 2024

Random forest - combining CA + CO data

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

#list of pollutants to model
pollutants = ['O3']

#list of location ranges
state = ['CA','CO']

#use bagging?
bagging = 'yes'

#list of pods to model
CAlocations = ['AFRC','TMF','Whittier','Ames','Richmond','SJSU']
CApods = ['YPODR9','YPODA2','YPODA7','YPODL6','YPODL1','YPODL9']

COlocations = ['BAO','NREL','Platteville']
COpods = ['YPODD8','YPODF1','YPODF9']

#create a directory path for us to pull from / save to
CApath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Modeling Surface Concentrations'
COpath = 'C:\\Users\\okorn\\Documents\\FRAPPE (2024 Modeling)'

for n in range(len(pollutants)):
    #Create a blank dataframe to hold all our CA input data
    CAdata = pd.DataFrame()
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
   
        #combine our datasets - both already in local time
        xCA=pd.merge(ann_inputs,pod,left_index=True,right_index=True)
        #remove NaNs
        xCA = xCA.dropna()
        
        #Remove whitespace from column labels
        xCA.columns = xCA.columns.str.strip()
        
        #add an identifier - just for our use
        #xCA['location'] = '{}'.format(CAlocations[k])
        
        #add the data from this pod & Pandora to the overall dataframe
        CAdata = pd.concat([CAdata,xCA],ignore_index=False)
        
    #-------------------------------------  
    #Create a blank dataframe to hold all our CO input data
    COdata = pd.DataFrame()
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
        
        #add an identifier - just for our use
        #xCO['location'] = '{}'.format(COlocations[j])
        
        #add the data from this pod & Pandora to the overall dataframe
        COdata = pd.concat([COdata,xCO],ignore_index=False)
        
    #-------------------------------------
    #make a common 'x' with all our data
    x = pd.concat([CAdata,COdata],ignore_index=True)
            
    #now for reformatting - get our 'y' data alone
    y = pd.DataFrame(x.pop('Y_hatfield'))
        
    #Now do our test-train split
    X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=.2)

    #Create a Random Forest regressor object
    rf_regressor = RandomForestRegressor()
    
    if bagging == 'yes':
        # Create a BaggingRegressor with the base model
        rf_regressor = BaggingRegressor(rf_regressor)

        
    #Train the Random Forest regressor on the training data
    rf_regressor.fit(X_train, y_train)
        
    # make predictions
    y_hat_train = rf_regressor.predict(X_train)
    y_hat_test = rf_regressor.predict(X_test)
        
    #now add the predictions  & y's back to the original dataframes
    X_train['y_hat_train'] = y_hat_train
    X_test['y_hat_test'] = y_hat_test
    X_train['Y'] = y
    
    if bagging == 'no':
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
    if bagging == 'yes':    
        #Name a new subfolder
        subfolder_name = 'Outputs_allCOCA_{}_bag_rf'.format(pollutants[n])
    else:
        subfolder_name = 'Outputs_allCOCA_{}_rf'.format(pollutants[n])
    #Create the subfolder path
    subfolder_path = os.path.join(CApath, subfolder_name)
    #Create the subfolder
    os.makedirs(subfolder_path, exist_ok=True)

    #save out the final data
        
    #X_train
    savePath = os.path.join(subfolder_path,'allCACO_X_train_{}.csv'.format(pollutants[n]))
    X_train.to_csv(savePath)
        
    #X_test
    savePath = os.path.join(subfolder_path,'allCACO_X_test_{}.csv'.format(pollutants[n]))
    X_test.to_csv(savePath)
    
    if bagging == 'no':
        #Importance labels
        savePath = os.path.join(subfolder_path,'allCACO_Factor_importance_{}.csv'.format(pollutants[n]))
        # Convert the dictionary to a DataFrame
        importance_labels = pd.DataFrame.from_dict(importance_labels, orient='index', columns=['Value'])
        importance_labels.to_csv(savePath)
        
    #Stats_train
    savePath = os.path.join(subfolder_path,'allCACO_stats_train_{}.csv'.format(pollutants[n]))
    # Convert the dictionary to a DataFrame
    stats_train = pd.DataFrame.from_dict(stats_train, orient='index', columns=['Value'])
    stats_train.to_csv(savePath)
        
    #Stats_test
    savePath = os.path.join(subfolder_path,'allCACO_stats_test_{}.csv'.format(pollutants[n]))
    # Convert the dictionary to a DataFrame
    stats_test = pd.DataFrame.from_dict(stats_test, orient='index', columns=['Value'])
    stats_test.to_csv(savePath)
        
    #Save the rf model itself
    savePath = os.path.join(subfolder_path,'allCACO_rfmodel_{}.joblib'.format(pollutants[n]))
    dump(rf_regressor, savePath)