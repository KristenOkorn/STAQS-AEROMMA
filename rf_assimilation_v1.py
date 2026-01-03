# -*- coding: utf-8 -*-
"""
Created on Tue Dec 30 07:34:42 2025

HCHO version (do O3 separately)

Load in ISNTEP, regulatory, WRF, & TEMPO data 

First tried with y as INSTEP surface estimate - best R2 was grid searched rf (0.1)
Now flipping to make y = wrf_srf - works well! GBR R²: 0.815 w/ INSTEP as an input
GBR with y = wrf_srf - drops slightly to GBR R²: 0.811 w/out INSTEP as an input
Standard RF (no grid search) - R2 = 0.876 w/ INSTEP as an input
Standard RF (no grid search) - R2 = 0.801 w/out INSTEP as an input

@author: okorn
"""

#Import basic toolboxes
import pandas as pd
import os
import numpy as np

#Import tools for loading in data
import gzip
import shutil
import xarray as xr
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

#Load in packages for ML model fitting
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor 
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.linear_model import Lasso

#load in previously generated parquet file?
load_parquet = 'yes'

if load_parquet == 'yes':
    #load in the previously generated parquet file
    final = pd.read_parquet("C:\\Users\\okorn\\Documents\\2023 AEROMMA\\final.parquet")
    
else: #if not, need to loop through and load in all the data

    #select level of tempo data to use
    level = 'L3'
    
    #----Get set up for the ground data----
    
    #need to pluck out just the lat/lon pairs that are relevant to each pod location
    podlocations = ['TMF','Whittier','AFRC','Caltech']
    podlatitudes = [34.38189,33.97676,34.95991,34.13685]
    podlongitudes = [-117.67809,-118.03032,-117.88107,-118.12608]
    pods = ['YPODA2','YPODA7','YPODR9','YPODG5']
    
    #split into pods vs scaqmd
    slocations = ['St Anthony','Manhattan Beach','Guenser Park','Elm Avenue','Judson', 'St Luke','Hudson','Inner Port','First Methodist','Harbor Park']#'AFRC','Caltech',
    slatitudes = [33.9185,33.89011,33.87049,33.83718,33.82494,33.81917,33.80229,33.78136,33.78199,33.78607]#34.95991,34.13685,
    slongitudes = [-118.40796,-118.4016,-118.3129,-118.33148,-118.26844,-118.21152,-118.22021,-118.21363,-118.26758,-118.2864]#-117.88107,-118.12608,
    
    #----------------------------------------------
    #Load the pod data - HCHO
    def process_pod(n):
        podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\R1 STAQS Field'
        #get the filename for the pod
        podfilename = "{}_HCHO_field_corrected.csv".format(pods[n])
        #read in the first worksheet from the workbook myexcel.xlsx
        podfilepath = os.path.join(podPath, podfilename)
        pod = pd.read_csv(podfilepath,index_col=0)  
        #remove any negatives
        pod = pod[pod.iloc[:, 0] >= 0]
        #Rename the index to match that of the pandora
        pod = pod.rename_axis('time')
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        pod.index = pd.to_datetime(pod.index,errors='coerce')
        #Change the pollutant column name
        pod.columns.values[0] = 'HCHO'
        #add the lat/lon to the dataframe
        pod['latitude'] = podlatitudes[n]
        pod['longitude'] = podlongitudes[n]
        #rename to make more clear
        pod.columns.values[1] = 'lat'
        pod.columns.values[2] = 'lon'
        #retime to hourly
        pod = pod.resample("1H").median()
        
        return pod
        
    with ThreadPoolExecutor() as exe:
        surface_pods = list(exe.map(process_pod, range(len(pods))))
       
    #----------------------------------------------
    
    #now repeat for the scaqmd data
    def process_scaqmd(k):
        scaqmdPath = 'C:\\Users\\okorn\\Documents\\2023 STAQS\\SCAQMD Data\\'
        #get the filename for the pod
        scaqmdfilename = "{}.csv".format(slocations[k])
        #read in the first worksheet from the workbook myexcel.xlsx
        scaqmdfilepath = os.path.join(scaqmdPath, scaqmdfilename)
        scaqmd = pd.read_csv(scaqmdfilepath,index_col=0)
        #make sure the ppb values are interpreted as numbers
        scaqmd.iloc[:, 0] = scaqmd.iloc[:, 0].replace('--', np.nan).astype(float)
        #remove any negatives
        scaqmd = scaqmd[scaqmd.iloc[:, 0] >= 0]
        #Rename the index to match that of the pandora
        scaqmd = scaqmd.rename_axis('datetime')
        #Convert the index to a DatetimeIndex and set the nanosecond values to zero
        scaqmd.index = pd.to_datetime(scaqmd.index,format="%m/%d/%Y %H:%M:%S %p",errors='coerce')
        #convert from pst to utc
        scaqmd.index += pd.to_timedelta(7, unit='h')
        #Change the pollutant column name
        scaqmd.columns.values[0] = 'HCHO'
        #add the lat/lon to the dataframe
        scaqmd['latitude'] = slatitudes[k]
        scaqmd['longitude'] = slongitudes[k]
        #rename to make more clear
        scaqmd.columns.values[1] = 'lat'
        scaqmd.columns.values[2] = 'lon'
        #retime to hourly
        scaqmd = scaqmd.resample("1H").median()
        
        return scaqmd
        
    #now combine the parallel outputs
    with ThreadPoolExecutor() as exe:
        surface_scaqmd = list(exe.map(process_scaqmd, range(len(slocations))))    
    
    #combine all our surface data into one list
    surface = surface_pods + surface_scaqmd
    #----------------------------------------------
    #now load in the cached tempo data
        
    #Choose domain for TEMPO data
    if level == 'L2':
        locname = 'LAbasin'
    elif level == 'L3':
        locname = 'LAbasinL3'
    elif level == 'L4':
        locname = 'LAbasinL4'
    
    #get path to level selected
    folder = Path('C:\\Users\\okorn\\Documents\\2023 STAQS\\{}'.format(locname))
    #get the list of .nc.gz files in this path
    gz_files = list(folder.glob("*.nc.gz"))
    #also get the list of files that are just .nc
    nc_files = list(folder.glob("*.nc"))
    
    #list to hold tempo data
    tempo = []
    
    #set up the process to loop through
    def process_gz_file(gz_path):
        #removes .gz, leaving .nc
        nc_path = gz_path.with_suffix("")  
        #decompress the file
        with gzip.open(gz_path, "rb") as f_in, open(nc_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        #open the file as ds
        ds = xr.open_dataset(nc_path)
     
        return ds
    
    def process_nc_file(nc_path):
        return xr.open_dataset(nc_path)
    
    with ThreadPoolExecutor() as exe:
        #decompress .gz files
        tempo_gz = list(exe.map(process_gz_file, gz_files))
        # pen plain .nc files
        tempo_nc = list(exe.map(process_nc_file, nc_files))
    
    #combine gz & nc files
    tempo = tempo_gz + tempo_nc
        
    #----------------------------------------------
    #now load in the cached wrf data
    
    #get the path to wrf
    folder = Path('C:\\Users\\okorn\\Documents\\2023 AEROMMA\\WRF')
    #get the lit of netcdf file in the directory
    nc_files = sorted(folder.glob("*.nc"))
    
    #get only the variables we need
    wrf_vars = ['Times','HCHO_SFC','LU_INDEX','PBLH','PSFC','T2','U10','V10']
    #time, surf hcho, land use, pblh, surf press, pot temp, temp @ 2m, u, u @ 10m, v, v @10m
    #leave out T (pot temp), U, V - too large as 3D
    
    def load_file(f):
        return xr.open_dataset(f)[wrf_vars]
    
    #load in the files
    with ThreadPoolExecutor() as exe:
        wrf_temp = list(exe.map(load_file, nc_files))
    
    #test to see all the variable names
    #list(wrf_temp[0].data_vars)
    #try accessing the data
    #wrf_temp[0]['HCHO_SFC'] 
    
    #combine into one larger dataset
    wrf = xr.concat(wrf_temp, dim="time")
    
    #----------------------------------------------
    #Now that all data is loaded in, reformat to a common grid (use TEMPO grid)
    
    #get the grid from the first tempo file
    lat_grid = tempo[0]['LATITUDE'][0, 0, :, :].values  # shape (12, 12)
    lon_grid = tempo[0]['LONGITUDE'][0, 0, :, :].values
    
    #loop though each TEMPO file to get the HCHO data & flatten it into the right shape
    
    all_tempo = []
    
    #get datetime from tflag
    def decode_ioapi_time(ds):
        tflag = ds['TFLAG'].values  # (TSTEP, VAR, 2)
    
        times = []
        for t in range(tflag.shape[0]):
            yyyyddd = tflag[t, 0, 0]
            hhmmss  = tflag[t, 0, 1]
    
            year = yyyyddd // 1000
            doy  = yyyyddd % 1000
    
            hour   = hhmmss // 10000
            minute = (hhmmss % 10000) // 100
            second = hhmmss % 100
    
            times.append(
                pd.Timestamp(year=year, month=1, day=1)
                + pd.Timedelta(days=doy - 1,
                                hours=hour,
                                minutes=minute,
                                seconds=second)
            )
    
        return pd.DatetimeIndex(times)
    
    
    for ds in tempo:
        # Extract feature
        feature = ds['VERTICAL_COLUMN'][:, 0, :, :]  # (TSTEP, ROW, COL)
    
        # Decode real datetimes
        times = decode_ioapi_time(ds)
    
        rows = []
        for t, time in enumerate(times):
            df = pd.DataFrame({
                'time': time,
                'lat': lat_grid.ravel(),
                'lon': lon_grid.ravel(),
                'VERTICAL_COLUMN': feature[t].values.ravel()
            })
            rows.append(df)
    
        all_tempo.append(pd.concat(rows, ignore_index=True))
    
    # Combine all datasets into one large DataFrame
    tempo_final = pd.concat(all_tempo, ignore_index=True)
    
    #define grid time mapping
    
    #----------------------------------------------
    #now flatten & reformat surface to match TEMPO - this will be our "Y"
    
    #empty list to hold reformatted surfce data
    surface_final = pd.DataFrame()
    
    for df in surface:
        df = df.reset_index()
        #Combine all datasets into one large DataFrame
        surface_final = pd.concat([surface_final, df], ignore_index=True)
        
    #drop any residual columns    
    surface_final = surface_final.drop(['datetime', 'latitude', 'longitude'],axis=1)
    
    #----------------------------------------------
    #now flatten & reformat WRF to match TEMPO - additional inputs
    
    
    # 1. Extract WRF times (robust)
    # Take first spatial element for each time step
    wrf_times = pd.to_datetime(
        [
            ''.join(
                c.decode('utf-8') if isinstance(c, bytes) else str(c)
                for c in t[0]
            ).strip().replace('_', ' ')
            for t in wrf['Times'].values
        ],
        errors='coerce'
    )
    
    # Convert to numpy datetime64 (CRITICAL)
    wrf_times = wrf_times.to_numpy(dtype='datetime64[ns]')
    
    # 2. Prepare grid
    lat_grid = wrf['XLAT'].values.astype('float32')
    lon_grid = wrf['XLONG'].values.astype('float32')
    
    n_times  = len(wrf_times)
    n_points = lat_grid.size
    
    # 3. Variables to extract
    wrf_vars_2 = [
        'HCHO_SFC',
        'LU_INDEX',
        'PBLH',
        'PSFC',
        'T2',
        'U10',
        'V10']
    
    # 4. Vectorized column construction
    time_col = np.repeat(wrf_times, n_points)
    lat_col  = np.tile(lat_grid.ravel(), n_times)
    lon_col  = np.tile(lon_grid.ravel(), n_times)
    
    data = {
        'time': time_col,
        'lat': lat_col,
        'lon': lon_col}
    
    # 5. Add WRF variables (vectorized)
    for var in wrf_vars_2:
        vals = wrf[var].values.reshape(n_times, -1)
        
        if var == 'HCHO_SFC':
            vals = vals * 1000  # convert to ppb
        
        data[var] = vals.ravel().astype('float32')
    
    # 6. Build DataFrame
    wrf_final = pd.DataFrame(data)
    
    # 7. Final sanity check
    print(wrf_final.info())
    print(wrf_final['time'].min(), '→', wrf_final['time'].max())
    
    #----------------------------------------------
    
    #now combine TEMPO & WRF on time, lat, and lon - X's
    
    from scipy.spatial import cKDTree
    
    def to_seconds(df, t0=None):
        if t0 is None:
            t0 = df['time'].min()
        return (df['time'] - t0).dt.total_seconds(), t0
    
    TIME_TOL = 1800       # seconds (30 min)
    LAT_TOL  = 0.05 #~5km
    LON_TOL  = 0.5 #~5km
    
    #build kd tree on the WRF data
    
    t1_sec, t0 = to_seconds(tempo_final)
    t2_sec, _  = to_seconds(wrf_final, t0)
    t3_sec, _  = to_seconds(surface_final, t0)
    
    scale = np.array([TIME_TOL, LAT_TOL, LON_TOL])
    
    tree2 = cKDTree(
        np.column_stack([
            t2_sec / scale[0],
            wrf_final['lat'].values / scale[1],
            wrf_final['lon'].values / scale[2]
        ])
    )
    
    #query wrf_final from tempo_final
    query_pts = np.column_stack([
        t1_sec / scale[0],
        tempo_final['lat'].values / scale[1],
        tempo_final['lon'].values / scale[2]
    ])
    
    dist, idx = tree2.query(query_pts, k=1)
    
    matched = dist <= 1.0   # within tolerance sphere
    
    #merge wrf_final from tempo_final
    df12 = tempo_final.loc[matched].copy()
    
    #get the wrf vars
    vars_from_wrf = ['time','HCHO_SFC','LU_INDEX','PBLH','PSFC','T2','U10','V10']
    
    df12[vars_from_wrf] = (
        wrf_final.iloc[idx[matched]][vars_from_wrf]
        .reset_index(drop=True)
    )
    df12['time_wrf_final'] = wrf_final.iloc[idx[matched]]['time'].values
    
    #build kd tree on the surface data
    tree3 = cKDTree(
        np.column_stack([
            t3_sec / scale[0],
            surface_final['lat'].values / scale[1],
            surface_final['lon'].values / scale[2]
        ])
    )
    
    query_pts = np.column_stack([
        (df12['time'] - t0).dt.total_seconds() / scale[0],
        df12['lat'].values / scale[1],
        df12['lon'].values / scale[2]
    ])
    
    dist, idx = tree3.query(query_pts, k=1)
    
    matched = dist <= 1.0
    
    final = df12.loc[matched].copy()
    final['HCHO'] = surface_final.iloc[idx[matched]]['HCHO'].values
    
    #ve out for future ue
    final.to_parquet("final.parquet",engine="pyarrow",compression="snappy")

#----------------------------------------------
#now reformat to put into rf model

#get the key columns on their own - will need these back later
keys = final[['time', 'lat', 'lon']].copy()
#save out to file to make sure we don't lose them

#drop missing values
final = final.dropna()

#get our y's on their own - surface HCHO
y = final['HCHO_SFC'].copy()

#drop any unnescessary columns from final df
x = final.drop(columns=['time','time_wrf_final','HCHO_SFC'])
#x = final.drop(columns=['time','lat','lon','time_wrf_final','HCHO'])

#make x a series rather than dataframe
x_array = x.to_numpy()

# Split into train and test (80% train, 20% test)
X_train, X_test, y_train, y_test = train_test_split(x_array, y, test_size=0.2, random_state=42)

#----------------------------------------------
#run a standard rf model (faster but can be improved w gridsearch)

# Initialize Random Forest
rf = RandomForestRegressor(
    n_estimators=100,       # number of trees
    max_depth=None,         # no maximum depth
    random_state=42
)

# Train the model
rf.fit(X_train, y_train)

# Predict on test set
y_pred = rf.predict(X_test)

# Evaluate
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Standard RF MSE: {mse:.3f}")
print(f"Standard RF R^2: {r2:.3f}")

#----------------------------------------------
#run the rf model with gridsearch for parameter tuning (slow)

param_grid = {
    'n_estimators': [100, 300, 500],
    'max_depth': [None, 5, 10, 20],
    'min_samples_split': [2, 5, 10],
    'max_features': ['auto', 'sqrt', 0.5]
}

rf = RandomForestRegressor(random_state=42)
grid = GridSearchCV(rf, param_grid, cv=5, n_jobs=-1, scoring='r2')
grid.fit(X_train, y_train)

print("Best params:", grid.best_params_)
print("CV best R²:", grid.best_score_)

# Predict on test set
y_pred = rf.predict(X_test)

# Evaluate
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

#----------------------------------------------
#assess feature importances

# Get feature importances
importances = rf.feature_importances_
feature_names = x.columns

# Create a DataFrame for easy viewing
feat_imp = pd.DataFrame({'feature': feature_names, 'importance': importances})
feat_imp = feat_imp.sort_values(by='importance', ascending=False)

#----------------------------------------------
#interaction terms did not improve fits - skip this
#----------------------------------------------
#try gradient boosting instead

gbr = GradientBoostingRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=3,
    subsample=0.8,
    random_state=42
)

gbr.fit(X_train, y_train)
y_pred_gb = gbr.predict(X_test)

print("GBR R²:", r2_score(y_test, y_pred_gb))
print("GBR MSE:", mean_squared_error(y_test, y_pred_gb))

#----------------------------------------------
#try ridge instead

#need to do scaling first
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

#now try ridge

ridge = Ridge(alpha=1.0)
ridge.fit(X_train_s, y_train)

y_pred_ridge = ridge.predict(X_test_s)

print("Ridge R²:", r2_score(y_test, y_pred_ridge))

#----------------------------------------------
#try lasso instead

lasso = Lasso(alpha=0.01, max_iter=10000)
lasso.fit(X_train_s, y_train)

y_pred_lasso = lasso.predict(X_test_s)

print("Lasso R²:", r2_score(y_test, y_pred_lasso))

