# -*- coding: utf-8 -*-
"""
Created on Wed Apr 30 06:02:55 2025

Plot Pearson Coefficients for pod + pandora data

Surface vs tropo pandora

Various levels of data cleaning for Pandora

@author: okorn
"""

#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import scipy.stats as stats
import matplotlib.cm as cm

#get the relevant location data for each
locations = ['Whittier','TMF','AFRC'] 
pods = ['YPODA7','YPODA2','YPODR9'] 

#create places to hold all our values
corrs = np.zeros((4, 3))
nums = np.zeros((4, 3))

for n in range(len(locations)): 
       
    #-------------------------------------
    #Do the tropo Pandora data first
    pandoraPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\Pandora 2023'
    #get the filename for pandora
    pandorafilename = "{}_tropo_extra_HCHO.csv".format(locations[n])
    #join the path and filename
    pandorafilepath = os.path.join(pandoraPath, pandorafilename)
    #now read in the data
    pandora2 = pd.read_csv(pandorafilepath,index_col=1)
    #Reset the seconds to zero in the index
    pandora2.index = pandora2.index.str.replace(r'\d{2}$', '00')
    #Convert the index to a DatetimeIndex
    pandora2.index = pd.to_datetime(pandora2.index)#rename index to datetime
    pandora2 = pandora2.rename_axis('datetime')
    #Filter so the lowest quality flag is omitted
    pandora2 = pandora2.loc[pandora2['quality_flag'] != 12]
    #and convert to ppb
    pandora2['HCHO'] = pandora2['HCHO']*0.08206*pandora2['temperature']*1000/(pandora2['max_vert_tropo'])
    
    #for additional filtering, get the high quality data alone
    pandora_high = pandora2[pandora2['quality_flag'] == 10]
    #now get the mean indep uncertainty for the high values
    high_mean = pandora_high['independent_uncertainty'].mean()
    #and the standard deviation
    high_std = pandora_high['independent_uncertainty'].std()
    #now calculate the cut-off value from this
    cutoff = high_mean + (3*high_std)
    #now apply this filtering as a new dataframe
    pandora_filtered = pandora2[pandora2['independent_uncertainty'] < cutoff]
    #convert the filtered data from mol/m2 to ppb
    pandora_filtered['HCHO'] = pandora_filtered['HCHO']*0.08206*pandora_filtered['temperature']*1000/(pandora_filtered['max_vert_tropo'])
    
    #-------------------------------------
    #now load in the surface pandora data

    #get the filename for pandora
    surfpandorafilename = "{}_surface_extra_HCHO.csv".format(locations[n])
    #join the path and filename
    surfpandorafilepath = os.path.join(pandoraPath, surfpandorafilename)
    surfpandora = pd.read_csv(surfpandorafilepath,index_col=1)
    #Reset the seconds to zero in the index
    surfpandora.index = surfpandora.index.str.replace(r'\d{2}$', '00')
    #Convert the index to a DatetimeIndex
    surfpandora.index = pd.to_datetime(surfpandora.index)#rename index to datetime
    surfpandora = surfpandora.rename_axis('datetime')
    #Filter to only use high quality data
    surfpandora = surfpandora.loc[surfpandora['quality_flag'] != 12]
    #and convert to ppb
    surfpandora['HCHO'] = surfpandora['HCHO']*0.08206*surfpandora['temperature']*1000/(surfpandora['max_vert_tropo'])
    
    #for additional filtering, get the high quality data alone
    surfpandora_high = surfpandora[surfpandora['quality_flag'] == 10]
    #now get the mean indep uncertainty for the high values
    surfhigh_mean = surfpandora_high['surface_uncertainty'].mean()
    #and the standard deviation
    surfhigh_std = surfpandora_high['surface_uncertainty'].std()
    #now calculate the cut-off value from this
    cutoff = surfhigh_mean + (3*surfhigh_std)
    #now apply this filtering as a new dataframe
    surfpandora_filtered = surfpandora[surfpandora['surface_uncertainty'] < cutoff]
    #convert the filtered data from mol/m2 to ppb
    surfpandora_filtered['HCHO'] = surfpandora_filtered['HCHO']*0.08206*surfpandora_filtered['temperature']*1000/(surfpandora_filtered['max_vert_tropo'])
    
    #-------------------------------------
    podPath = 'C:\\Users\\okorn\\Documents\\2023 Deployment\\RB STAQS Field 2024'
    #get the filename for the pod
    podfilename = "{}_HCHO.csv".format(pods[n])
    #read in the first worksheet from the workbook myexcel.xlsx
    podfilepath = os.path.join(podPath, podfilename)
    pod = pd.read_csv(podfilepath,index_col=0)  
    #remove any negatives
    pod = pod[pod.iloc[:, 0] >= 0]
    #Rename the index to match that of the pandora
    pod = pod.rename_axis('datetime')
    #Convert the index to a DatetimeIndex and set the nanosecond values to zero
    pod.index = pd.to_datetime(pod.index,format="%d-%b-%Y %H:%M:%S",errors='coerce')
    #Change the pollutant column name
    pod.columns.values[0] = 'INSTEP HCHO'

    #-------------------------------------
    
    #loop through all 4 dataframes to reformat & calculate
    df_list = [pandora2, pandora_filtered, surfpandora, surfpandora_filtered]
    for k in range(len(df_list)):
        #get the df (we need numeric for plotting later)
        df = df_list[k]
        #first get the times from the pandora we want to merge to
        df_merge = pd.merge_asof(df, pod, on='datetime', direction='nearest')
        #delete the columns we don't need
        df_merge = df_merge.iloc[:, list(range(3)) + list(range(-2, 0))]
        #drop any NaNs so we have an accurate count of n
        df_merge = df_merge.dropna()
        #now calculate the pearson's coefficient for this location
        corr, p_value = stats.pearsonr(df_merge['INSTEP HCHO'], df_merge['HCHO'])
        
        #now save this value to the corresponding place in a list for later plotting
        corrs[k,n] = corr
        nums [k,n] = len(df_merge)
     
#-------------------------------------
    
#initialize a plot to hold all of our results
fig, axes = plt.subplots(2, 1,figsize=(6, 4))  # 2 subplots stacked vertically

#Choose a colormap
cmap = plt.cm.bwr
#Normalize data values for coloring
norm = plt.Normalize(-1, 1)
sm = cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])  # required dummy array for the colorbar

def draw_grid(ax, values, counts):
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 2)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.invert_yaxis()  # optional: origin at top-left

    for row in range(2):
        for col in range(3):
            val = values[row, col]
            num = nums[row, col]
            color = cmap(norm(val))
            rect = plt.Rectangle((col, row), 1, 1, color=color)
            ax.add_patch(rect)
            #add main text
            ax.text(col + 0.5, row + 0.5, f"{round(val, 2)}", color='black',
                    ha='center', va='center', fontsize=14)
            #add count of n
            ax.text(col + 0.95, row + 0.05, f"n={int(num)}",
                    color='black', ha='right', va='top', fontsize=8)

# Split the 6x4 array into two 2x3 arrays
top_values = corrs[0:2, 0:3]  # First 2 rows, first 3 columns (2x3 grid)
bottom_values = corrs[2:4, 0:3]  # Last 2 rows, last 3 columns (2x3 grid)

#and do the same for the counts data
top_counts = nums[0:2, 0:3]      # shape (2, 3)
bottom_counts = nums[2:4, 0:3]   # shape (2, 3)

# Draw both grids (top and bottom plots)
draw_grid(axes[0], top_values, top_counts)  # For the top subplot (2x3)
draw_grid(axes[1], bottom_values, bottom_counts)  # For the bottom subplot (2x3)

# Add shared colorbar on the right
cbar_ax = fig.add_axes([1, 0.15, 0.02, 0.7])  # [left, bottom, width, height]
fig.colorbar(sm, cax=cbar_ax, label="Pearson Correlation")

# Get position of bottom subplot in figure coordinates
bbox = axes[1].get_position()
x0, width = bbox.x0, bbox.width
y_bottom = bbox.y0

# Place labels under each column of the bottom plot
for i, label in enumerate(locations):
    x = x0 + (i + 0.5) * (width / 3)
    fig.text(x+0.1, y_bottom - 0.1, label, ha='center', va='top', fontsize=12)

#framework for adding labels to the tops of each subplot
def add_top_label(ax, label, ncols):
    ax.text(ncols / 2, -0.1, label,  # -0.3 positions above the top (invert_yaxis makes this work)
            ha='center', va='bottom', fontsize=14, fontweight='bold', transform=ax.transData)

#now call it to plot the subplot labels
add_top_label(axes[0], "Pandora Tropospheric Column", ncols=3)
add_top_label(axes[1], "Pandora Surface Estimate", ncols=3)

#framework for adding row labels
def add_row_labels(ax, labels):
    for row in range(len(labels)):
        ax.text(-0.02, row + 0.5, labels[row], 
                ha='right', va='center', fontsize=12, transform=ax.transData)
        
#now call it to plot the row labels
add_row_labels(axes[0], ["Low Quality", "Indep. Uncert."])
add_row_labels(axes[1], ["Low Quality", "Indep. Uncert."])

plt.tight_layout()
plt.subplots_adjust(hspace=0.3)  # Adjust vertical spacing between subplots
plt.show()