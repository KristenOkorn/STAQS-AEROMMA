# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 13:28:10 2025

Calculate the surface and column cutoff uncertainty

For AGES+ locations only - TMF, Whittier & AFRC

Note: none of these have high quality data
So this doesn't work

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import os

#loop through locations & pollutants
locations = ['AFRC','Whittier','TMF']
pollutant = 'HCHO'

for n in range(len(locations)): 
    
    #-------------------------------------
    #load in the pandora tropo csv's 
    pandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
    #get the filename for pandora
    pandorafilename = "{}_tropo_extra_HCHO.csv".format(locations[n])
    #join the path and filename
    pandorafilepath = os.path.join(pandoraPath, pandorafilename)
    pandora = pd.read_csv(pandorafilepath,index_col=1)
    #Reset the seconds to zero in the index
    pandora.index = pandora.index.str.replace(r'\d{2}$', '00',regex=True)
    #Convert the index to a DatetimeIndex
    pandora.index = pd.to_datetime(pandora.index)#rename index to datetime
    pandora = pandora.rename_axis('datetime')
    #Filter so that only the highest quality data is included
    pandora = pandora.loc[pandora['quality_flag'] == 0]
    #just keep 2023 data
    pandora = pandora[pandora.index.year == 2023]
    
    #-------------------------------------
    #next load in the pandora surface csv's - skip for non-pandora sites
    surfpandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
    #get the filename for pandora
    surfpandorafilename = "{}_surface_extra_HCHO.csv".format(locations[n])
    #join the path and filename
    surfpandorafilepath = os.path.join(surfpandoraPath, surfpandorafilename)
    surfpandora = pd.read_csv(surfpandorafilepath,index_col=1)
    #Reset the seconds to zero in the index
    surfpandora.index = surfpandora.index.str.replace(r'\d{2}$', '00')
    #Convert the index to a DatetimeIndex
    surfpandora.index = pd.to_datetime(surfpandora.index)#rename index to datetime
    surfpandora = surfpandora.rename_axis('datetime')
    #Filter for only high quality data
    surfpandora = surfpandora.loc[surfpandora['quality_flag'] == 0]
    #just keep 2023 data
    surfpandora = surfpandora[surfpandora.index.year == 2023]
    
    #-------------------------------------
    #now calculate the max uncertainty parameter for each
    tropo_uncert = pandora['independent_uncertainty'].mean(skipna=True) + 3*pandora['independent_uncertainty'].std(skipna=True)
    print("{} tropo uncert {}".format(locations[n], tropo_uncert))
    surf_uncert = surfpandora['surface_uncertainty'].mean(skipna=True) + 3*surfpandora['surface_uncertainty'].std(skipna=True)
    print("{} surface uncert {}".format(locations[n], surf_uncert))
    