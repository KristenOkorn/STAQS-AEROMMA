# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 03:36:52 2024

Runs separately for all matching surface-Pandora pairs

Using grid search for hyperparameter tuning

getting stuck on noaa / topaz

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import seaborn as sns
from datetime import datetime, timedelta
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import BaggingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import GridSearchCV
from joblib import dump, load
from sklearn.preprocessing import StandardScaler


#list of pollutants to model
pollutants = ['O3']
#datatype will vary based on pollutant
dtype = ['column']

#use bagging?
bagging = 'no'

#list of pods to model
locations = ['Bayonne','Bristol','Bronx','CapeElizabeth','Cornwall','EastProvidence','Londonderry','Lynn','MadisonCT','NewBrunswick','NewHaven','OldField','Philadelphia','Pittsburgh','Queens','WashingtonDC','Westport','AFRC','TMF','Ames','Richmond','CSUS','NOAA','SLC','BAO','NREL','Platteville','AldineTX','LibertyTX','HoustonTX']
pods = ['EPA_Bayonne','EPA_Bristol','EPA_Bronx','EPA_CapeElizabeth','EPA_Cornwall','EPA_EastProvidence','EPA_Londonderry','EPA_Lynn','EPA_MadisonCT','EPA_NewBrunswick','EPA_NewHaven','EPA_OldField','EPA_Philadelphia','EPA_Pittsburgh','EPA_Queens','EPA_WashingtonDC','EPA_Westport','YPODR9','YPODA2','YPODL6','YPODL1','YPODL2','topaz','WBB','YPODD4','YPODF1','YPODF9','HoustonAldine','LibertySamHoustonLibrary','UHMoodyTower']

#create a directory path for us to pull from / save to
path = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Modeling Surface Concentrations\\All O3 Data Combined'

for n in range(len(pollutants)):
    for k in range(len(locations)):
        #load the Pandora (ML input) data
        filename = "{}_{}_extra_{}.csv".format(locations[k],dtype[n],pollutants[n])
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
        
        #resample to hourly - since pod data will be minutely
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
        
        #data cleaning - remove negatives from the O3 column
        ann_inputs.loc[ann_inputs['O3'] < 0, 'O3'] = np.nan
        
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
        # Convert Index to DatetimeIndex
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
        
        #now for reformatting - get our 'y' data alone
        y = pd.DataFrame(x.pop('Y_hatfield'))
        
        #Now do our test-train split
        X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=.2)
        
        #scale our dataset
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        #Create a Random Forest regressor object
        rf_regressor = RandomForestRegressor()
        
        # Define a parameter grid to search over
        param_grid = {
            'n_estimators': [50, 100],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['auto', 'sqrt', 'log2'],
            }
        
        if bagging == 'no':
            #initialize the GridSearchCV object
            grid_search = GridSearchCV(rf_regressor, param_grid, cv=5, scoring='neg_mean_squared_error')

        elif bagging == 'yes':
            
            # Create a Bagging Regressor with the base Random Forest Regressor
            bagging_rf_model = BaggingRegressor(rf_regressor, random_state=42)

            # Create a pipeline with a scaler and the bagging regressor
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('bagging', bagging_rf_model)
                ])
            
            # Update the parameter grid for the pipeline
            param_grid_pipeline = {
                'bagging__base_estimator__n_estimators': [50, 100],
                'bagging__base_estimator__max_depth': [None, 10, 20],
                'bagging__base_estimator__min_samples_split': [2, 5, 10],
                'bagging__base_estimator__min_samples_leaf': [1, 2, 4],
                'bagging__base_estimator__max_features': ['auto', 'sqrt', 'log2'],
                'bagging__n_estimators': [10, 20],  # Number of base estimators in the ensemble
                'bagging__bootstrap_features': [True, False],
                }
            
            #Create the GridSearchCV object with BaggingRegressor
            grid_search = GridSearchCV(pipeline, param_grid_pipeline, cv=5, scoring='neg_mean_squared_error')
            
        # Fit the model to the data
        grid_search.fit(X_train_scaled, y_train['Y_hatfield'].values)
    
        #get the best parameters found
        best_params = grid_search.best_params_
        #convert the dictionary to a pandas DataFrame
        best_params = pd.DataFrame(best_params, index=['Value']).transpose()

        #get the best model
        best_rf_model = grid_search.best_estimator_
            
        # make predictions
        y_hat_train = best_rf_model.predict(X_train_scaled)
        y_hat_test = best_rf_model.predict(X_test_scaled)
        
        #now add the predictions  & y's back to the original dataframes
        X_train['y_hat_train'] = y_hat_train
        X_test['y_hat_test'] = y_hat_test
        X_train['Y'] = y_train
        X_test['Y'] = y_test
        
        if bagging == 'no':
            #Get the feature importances
            importances = best_rf_model.feature_importances_

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
        
        #save all of our results to file
        if bagging == 'yes':    
            #Name a new subfolder
            subfolder_name = 'Outputs_{}_rf_all_bag_grid'.format(pollutants[n])
        else:
            subfolder_name = 'Outputs_{}_rf_all_grid'.format(pollutants[n])
        
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
        
        if bagging == 'no':
            #Importance labels
            savePath = os.path.join(subfolder_path,'{}_{}.csv'.format(locations[k],pollutants[n]))
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
        
        #save the best parameters
        savePath = os.path.join(subfolder_path,'{}_params_{}.csv'.format(locations[k],pollutants[n]))
        best_params.to_csv(savePath)
        
        #save the best rf model
        savePath = os.path.join(subfolder_path,'{}_rfmodel_{}.joblib'.format(locations[k],pollutants[n]))
        dump(best_rf_model, savePath)