# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 08:44:39 2025

Reformat CARB ozone data 

@author: kokorn
"""

import os 
import pandas as pd
from datetime import datetime, date

#set the main path
input_dir = 'C:\\Users\\kokorn\\Documents\\2023 Deployment\\O3\\CARB O3\\Input'
output_dir = 'C:\\Users\\kokorn\\Documents\\2023 Deployment\\O3\\CARB O3\\Output'

site_dfs = {}  #dict to hold site info from all files

#for each file
for filename in os.listdir(input_dir):
    file_path = os.path.join(input_dir, filename)
    df = pd.read_csv(file_path, usecols=["date", "start_hour", "value","name "])
    #make a datetime column
    df["datetime"] = pd.to_datetime(df["date"]) + pd.to_timedelta(df["start_hour"], unit="h")
    #and drop the original columns
    df = df.drop(columns=["date", "start_hour"])
    #make the datetime column first
    df = df[["datetime"] + df.columns.drop("datetime").tolist()]
    
    #split into separate dataframes by site
    for site, data in df.groupby("name "):
       if site in site_dfs:
           #append and re-sort
           site_dfs[site] = pd.concat([site_dfs[site], data], ignore_index=True)
       else:
           site_dfs[site] = data.copy()

for site, df_site in site_dfs.items():
    #sort by time
    df_site = df_site.sort_values("datetime").reset_index(drop=True)
    #drop the original name column
    df_site = df_site.drop(columns=["name "])
    #convert to ppb
    df_site['value'] = df_site['value']*1000
    #rename the column to keep track
    df_site = df_site.rename(columns={"value": "O3_ppb"})
    #Make a clean filename (remove spaces, etc.)
    site_name = str(site).strip().replace(" ", "_")
    out_path = os.path.join(output_dir, f"{site_name}_O3.csv")
    df_site.to_csv(out_path, index=False)