# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 16:12:03 2023

Plot location data for pods & other variables - AEROMMA DC-8

@author: okorn
"""

#import libraries
import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
from tkinter.filedialog import askdirectory
import netCDF4 as nc

#import mapping library
import cartopy.crs as ccrs
import cartopy.feature as cf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates

#need to pluck out just the lat/lon pairs that are relevant to each pod location
locations = ['AFRC','TMF','Caltech','Whittier','Redlands']
latitudes = [34.95991,34.38189,34.13685,33.97676,34.05985]
longitudes = [-117.88107,-117.67809,-118.12608,-118.03032,-117.14573]
colors = ['b','g','r','c','m']

dates = ['2023-08-22','2023-08-23','2023-08-25','2023-08-26']

#load in the METNAV data - gives lat/lon
navPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\'
#get the filename for gcas
navfilename = "METNAV.csv"
#join the path and filename
navfilepath = os.path.join(navPath, navfilename)
nav = pd.read_csv(navfilepath,index_col=0)
#Convert the index to a DatetimeIndex and set the nanosecond values to zero
nav.index = pd.to_datetime(nav.index)
#Delete the columns we won't use
nav = nav.drop(nav.columns[[2,3]], axis=1)
# Drop rows containing the value -9999.0
nav = nav.loc[(nav != -9999.0).all(axis=1)]

#Do a separate plot for each day 
for i in range(len(dates)):
    
    #Convert the string to a datetime object
    date = datetime.strptime(dates[i], '%Y-%m-%d')
    
    #Mask the DataFrame to include only rows from the selected date
    masked_nav = nav[(nav.index >= date) & (nav.index <= date+timedelta(days=1)-timedelta(seconds=1))]

    # %% lat/lon map (colored by time)
    
    fig4 = plt.figure(4)
    
    projection = ccrs.Mercator()
    #projection = ccrs.Mercator(central_longitude=180) #else try this

    ax4 = plt.axes(projection=projection)
    
    #Add stock image with custom land and ocean colors
    ax4.stock_img()
    ax4.background_patch.set_facecolor('tan')  # Set land color
    ax4.add_feature(cf.OCEAN, edgecolor='none', facecolor='lightblue')  # Set ocean color
    
    ax4.add_feature(cf.COASTLINE)
    ax4.add_feature(cf.BORDERS)
    
    plate = ccrs.PlateCarree()
    
    #add the DC8 data first so it doesn't cover the pods
    ax4.scatter(masked_nav['Longitude'], masked_nav['Latitude'], c='gray', s=3, transform=plate,label='DC-8 Tracks')

    #next layer the pod data on top
    for k in range(len(locations)):
        ax4.scatter(longitudes[k], latitudes[k],c=colors[k], s=20, transform=plate, label='{}'.format(locations[k]))

    #Calculate the buffer values
    x_buffer = .2 * (max(masked_nav['Longitude']) - min(masked_nav['Longitude']))
    y_buffer = .2 * (max(masked_nav['Latitude']) - min(masked_nav['Latitude']))
        
    #Adjust the extent based on the buffer
    ax4.set_extent([min(masked_nav['Longitude']) - x_buffer, max(masked_nav['Longitude']) + x_buffer, min(masked_nav['Latitude']) - y_buffer, max(masked_nav['Latitude']) + y_buffer], crs=ccrs.PlateCarree())
    
    fig4.tight_layout()
    
    #Adding a title to fig4
    fig4.suptitle('DC-8 {}'.format(dates[i]), y=0.95)  # Adjust the vertical position (0 to 1)
    
    #add a legend
    ax4.legend(loc='upper left',fontsize='small')

    #Display the plot
    plt.show()
    
    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\Maps\\'
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'DC8_map_{}'.format(dates[i]))
    # Save the figure to a filepath
    fig4.savefig(savePath)