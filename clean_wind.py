# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 09:00:24 2026

Clean up the redlands met data (WU) for generating wind roses

@author: kokorn
"""

#import helpful toolboxes
import os 
import pandas as pd

#read in the redlands met data from local directory
path = 'C:\\Users\\kokorn\\Documents\\2023 AEROMMA\\2026 MET Data'
#get the current sg roster
file_path = os.path.join(path, 'Wrightwood_MET_WU.xlsx')
redlands = pd.read_excel(file_path)

#build the dictionary of compass directions
compass = {
    'N': 0,
    'NNE': 22.5,
    'NE': 45,
    'ENE': 67.5,
    'E': 90,
    'ESE': 112.5, 
    'SE': 135,
    'SSE': 157.5,
    'S': 180,
    'SSW': 202.5,
    'SW': 225,
    'WSW': 247.5,
    'W': 270,
    'WNW': 292.5,
    'NW': 315,
    'NNW': 337.5,
    'CALM': 'NaN'
}

#replace the directions with numeric values
redlands['Wind'] = redlands['Wind'].map(compass)

#now drop the ' mph' from the speed so we just have numeric
redlands['Wind Speed'] = redlands['Wind Speed'].str.replace(r'\s.*$', '', regex=True)

#combine date & time columns
redlands['datetime'] = redlands['date'] + pd.to_timedelta(redlands['Time'].astype(str))

#drop columns we no longer need
redlands = redlands.drop(columns=['date','Time','Temperature','Dew Point','Humidity','Wind Gust','Pressure','Precip.','Condition'])

#rename the wind columns
redlands = redlands.rename(columns={'Wind': 'wdir', 'Wind Speed': 'wspd_mph'})

#save to file
redlands.to_csv('C:\\Users\\kokorn\\Documents\\2023 AEROMMA\\2026 MET Data\\wrightwood_MET_cleaned.csv', index=False)