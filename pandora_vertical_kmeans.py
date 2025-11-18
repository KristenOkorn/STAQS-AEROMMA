# -*- coding: utf-8 -*-
"""
Created on Mon Nov 10 16:56:50 2025

Plot vertical pandora data to understand typical vertical profiles

Once kmeans is done, also try sklearn.ensemble.HistGradientBoostingClassifier and Regressor

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from scipy.cluster.vq import kmeans2
from scipy.spatial.distance import pdist, squareform

#get pandora locations only
locations = ['Whittier','AFRC','TMF']
pods = ['YPODA7','YPODR9','YPODA2']
colors = ["salmon", "skyblue", "lightgreen"]

#pool of how many shapes to start with
initial_num_means = 7  
#final number of how many most different shapes to plot
final_num_means = 4 #use this one if not differencing

#use scaling?
scaling = 'yes'
#use differencing to find the most different subset of centroids?
differencing = 'yes'

for n in range(len(locations)): 
    
    #load in the pandora vertical data
    pandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
    #get the filename for pandora
    pandorafilename = "{}_tropo_extra_HCHO.csv".format(locations[n])
    #join the path and filename
    pandorafilepath = os.path.join(pandoraPath, pandorafilename)
    pandora = pd.read_csv(pandorafilepath,index_col=1)
    #Reset the seconds to zero in the index
    pandora.index = pandora.index.str.replace(r'\d{2}$', '00')
    #Convert the index to a DatetimeIndex
    pandora.index = pd.to_datetime(pandora.index)#rename index to datetime
    pandora = pandora.rename_axis('datetime')
    #Filter so the lowest quality flag is omitted
    pandora = pandora.loc[pandora['quality_flag'] != 12]
    #get rid of times that don't have the vertical profile
    pandora = pandora.dropna()
    #drop unnessecarry columns - we need temp and the vertical profiles
    pandora = pandora.drop(pandora.columns[[0, 1, 2, 3, 5, 6, 7, 8]], axis=1)
    #put temperature in its own dataframe for cleaner handling
    ptemp = pd.DataFrame(pandora.pop('temperature'))
    #add a layer zero column
    pandora.insert(0, 'layer0', 0)
    #drop the top layer - i don't know how to handle the edge case
    pandora = pandora.iloc[:, :-1]
    
    #-----
    #Convert the layer heights
    for i in range(1, pandora.shape[1], 2):  # loop through odd columns
        if i - 1 >= 0 and i + 1 < pandora.shape[1]:
            left = pandora.iloc[:, i - 1]
            right = pandora.iloc[:, i + 1]
            multiplier = right - left
            #apply the full mol/m2 to ppb correction
            pandora.iloc[:, i] = pandora.iloc[:, i] * 0.08206 * ptemp['temperature'] / multiplier #taking out 1000 bc km vs m
    
    #convert km to m
    pandora.iloc[:, ::2] = pandora.iloc[:, ::2] * 1000
    
    #limit to just study dates
    pandora = pandora.loc['8-1-2023':'10-31-2023']
    
    #-------------------------------------
 
    #initialize figure - subplot for each day
    fig, axs = plt.subplots(1, final_num_means, figsize=(8, 3))
    
    #-------------------------------------    
    #reformat the pandora vertical data
    
    new_x = [] #to hold the converted values
    new_y = [] #to hold the converted altitudes
    
    for i in range(len(pandora)):
        #Odd-indexed columns
        x = pandora.iloc[i, 1::2].reset_index(drop=True)
        #Even-indexed columns
        y_temp = pandora.iloc[i, 0::2].reset_index(drop=True)
        #Average neighboring heights and drop last NaN
        y = (y_temp.shift(-1) + y_temp) / 2
        y = y[:-1]
        #append
        new_x.append(x)
        new_y.append(y)
        
    #some x's contain -inf and inf - need to drop these & the corresponding y
    clean_x = []
    clean_y = []

    for x_series, y_series in zip(new_x, new_y):
        arr = np.asarray(x_series)
        if np.isinf(arr).any():     # series is bad → skip both x and y
            continue
        clean_x.append(x_series)
        clean_y.append(y_series)

    # Interpolate and fill any NaNs in each 
    x_clean = [
        s.interpolate(limit_direction='both').fillna(method='bfill').fillna(method='ffill')
        for s in clean_x
        ]

    y_clean = [
        s.interpolate(limit_direction='both').fillna(method='bfill').fillna(method='ffill')
        for s in clean_y
        ]
   
    #stack x&y into 1 series
    X = np.vstack([
        np.concatenate([x_clean[i], y_clean[i]])
        for i in range(len(x_clean))
        ])
    
    #zscore scaling - see if this helps with getting multiple of the same shapes
    if scaling == 'yes':
        X_unscaled = np.copy(X)
        X = (X - np.nanmean(X, axis=0)) / np.nanstd(X, axis=0)

    #-------------------------------------
    if differencing == 'yes':
        #cluster the profile shapes using kmeans - simplest method
        centroids, labels = kmeans2(X, k=initial_num_means, minit='points')
    
        #Compute pairwise distances between centroids
        distances = squareform(pdist(centroids))  # shape (k,k)
        #Select final_num_means most distinct centroids
        selected = []
        #Pick the first centroid randomly
        selected.append(0)
    
        for _ in range(1, final_num_means):
            #Compute min distance of each candidate to already selected centroids
            min_dist_to_selected = np.min(distances[:, selected], axis=1)
            #Ignore already selected
            min_dist_to_selected[selected] = -1
            #Pick the centroid with the max distance to selected
            next_idx = np.argmax(min_dist_to_selected)
            selected.append(next_idx)
    
    else:
        #cluster the profile shapes using kmeans - simplest method
        centroids, labels = kmeans2(X, k=final_num_means, minit='points')
    
    #if scaling was used, now un-scale
    if scaling == 'yes':
        centroids = centroids * np.nanstd(X_unscaled, axis=0) + np.nanmean(X_unscaled, axis=0)
        
    if differencing == 'yes':
        centroid_x = centroids[selected][:, :int(centroids[selected].shape[1]/2)]
        centroid_y = centroids[selected][:, int(centroids[selected].shape[1]/2):]
        
    else: #normal way
        #separate out x and y coordinates from the centroids
        centroid_x = centroids[:, :int(centroids.shape[1]/2)]
        centroid_y = centroids[:, int(centroids.shape[1]/2):]
    
    #-------------------------------------
    #now plot the centroids (most common shapes), each on their own subplot
    for k in range(len(centroid_x)):
        #plot the data on this axis
        axs[k].plot(centroid_x[k],centroid_y[k],color=colors[n])
        #rotate xticks
        axs[k].tick_params(axis='x', rotation=45)
    
    #-------------------------------------
    # Increase horizontal spacing between subplots
    plt.subplots_adjust(wspace=0.5)
    #Increase vertical space between subplots
    plt.subplots_adjust(hspace=0.2, top=0.85, bottom=0.05)  # You can adjust the value as needed
    #rotate x-axis labels
    plt.xticks(rotation=45)  
    #Single y-axis label for all subplots
    fig.text(0.03, 0.5, 'Altitude (m)', va='center', rotation='vertical',fontsize=12)
    #Common x-axis label for all subplots
    fig.text(0.5, -0.05, 'HCHO (ppb)', ha='center',fontsize=12)
    #axs[-1].set_xlabel('HCHO (ppb)', ha='center',fontsize=12)
    #Add an overall title to the plot
    fig.text(0.5,0.91,'{}'.format(locations[n]), ha = 'center', fontsize=16, weight = 'bold')
    #add more padding to bottom
    fig.subplots_adjust(bottom=0.2) 
    
    #Display the plot
    plt.show()

    #save to a different folder so we don't confuse the script on the next iteration
    Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\ISAF HCHO Plots\\'
    #Create the full path with the figure name
    savePath = os.path.join(Spath,'altitude_Pandora_vert_{}'.format(locations[n]))
    #Save the figure to a filepath
    fig.savefig(savePath)

