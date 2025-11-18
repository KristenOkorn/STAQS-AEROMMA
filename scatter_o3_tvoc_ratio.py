# -*- coding: utf-8 -*-
"""
Created on Fri Oct  3 09:27:16 2025

XY Scatterplot of ozone and VOC ratio (HCHO / CH4)

INSTEP and airborne data - want to see if they have the same trend

@author: okorn
"""


#Import helpful toolboxes etc
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

#initialize figure - 1 plot per location
fig, axs = plt.subplots(1, 1, figsize=(10, 8))

#-------------------------------------
#load in the DC8 data    
#-------------------------------------
  
#load in the DC-8 in-situ data - Picarro CH4
picarrofilePath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\Picarro CO2 CH4 CO\\R0\\picarro.csv'
#read in the first worksheet from the workbook myexcel.xlsx
picarro = pd.read_csv(picarrofilePath,index_col=0)  
#Convert the index to a DatetimeIndex and set the nanosecond values to zero
picarro.index = pd.to_datetime(picarro.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
#split into separate ch4 file - helpful for handling missing data
picarroch4 = picarro
#remove any negatives for CH4 specifically
picarroch4 = picarroch4[picarroch4['CH4_ppb'] >= 0]
#Convert ppb to ppm for CH4
picarroch4['CH4_ppm'] = picarroch4['CH4_ppb']/1000

#load in the DC-8 in-situ data - ISAF HCHO
isafPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\ISAF HCHO\\R0\\ISAF_HCHO.csv'
#read in the first worksheet from the workbook myexcel.xlsx
isaf = pd.read_csv(isafPath,index_col=0)  
#remove any negatives
isaf = isaf[isaf.iloc[:, 0] >= 0]
#Convert the index to a DatetimeIndex and set the nanosecond values to zero
isaf.index = pd.to_datetime(isaf.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
#convert ppt to ppb
isaf[' CH2O_ISAF'] = isaf[' CH2O_ISAF']/1000
#now convert ppb to ppm
isaf[' CH2O_ISAF'] = isaf[' CH2O_ISAF']/1000

#load in the DC-8 in-situ data - CL O3
clPath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\CL O3\\CL_O3.csv'
#read in the first worksheet from the workbook myexcel.xlsx
cl = pd.read_csv(clPath,index_col=0)  
#remove any negatives
cl = cl[cl.iloc[:, 0] >= 0]
#Convert the index to a DatetimeIndex and set the nanosecond values to zero
cl.index = pd.to_datetime(cl.index,format="%Y-%m-%d %H:%M:%S",errors='coerce')
#re-average to minute to match pod
cl = cl.resample('1T').mean()

#load in the DC-8 MMS data - to color by altitude etc.
MMSpath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\MMS\\R0\\MMS.csv'
#read in the first worksheet from the workbook myexcel.xlsx
mms = pd.read_csv(MMSpath,index_col=0)  
#Convert the index to a DatetimeIndex and set the nanosecond values to zero
mms.index = pd.to_datetime(mms.index,errors='coerce')
#re-average to minute to match pod
mms = mms.resample('1T').mean()

#-------------------------------------
#get tVOC proxy      
#-------------------------------------
dc8 = pd.merge_asof(isaf, picarroch4, left_index=True, right_index=True, tolerance=pd.Timedelta('5T'),  direction='nearest')  
dc8 = pd.merge_asof(dc8, cl, left_index=True, right_index=True, tolerance=pd.Timedelta('5T'),  direction='nearest')  
dc8 = pd.merge_asof(dc8, mms, left_index=True, right_index=True, tolerance=pd.Timedelta('5T'),  direction='nearest')  

dc8['DC8 tVOC'] = dc8['CH4_ppm'] / dc8[' CH2O_ISAF']

dc8 = dc8.replace([np.inf, -np.inf], np.nan)
dc8 = dc8.dropna()

#for altitude, drop negatives
dc8['altitude'] = dc8['altitude'].where(dc8['altitude'] >= 0, np.nan)
    
#-------------------------------------
#Time to plot!     
#-------------------------------------
sc = axs.scatter(dc8['DC8 tVOC'], dc8['O3_CL'], label='DC-8', c='black',s=100)

#Set the font size of the tick labels
axs.tick_params(axis='both', labelsize=15)

# #Standardize the axes
axs.set_xlim(0, 400000)
axs.set_ylim(0, 100)

#-----Finishing touches for the overall figure-----    
#Single y-axis label for all subplots
fig.text(0.03, 0.5, 'O3 (ppb)', va='center', rotation='vertical',fontsize=16)
#Common x-axis label for all subplots
fig.subplots_adjust(bottom=0.10)  # increase the bottom margin
fig.text(0.5, 0.04, 'CH4 / HCHO', ha='center', va='center', fontsize=16)
#colorbar for altitude
#plt.colorbar(sc,label="Altitude (m)")  # add color scale

#Add a title with the date to each subplot
axs.set_title('DC-8 Chemiluminescence', y=.95,fontsize=20) 

#Display the plot
plt.show()

#save to a different folder so we don't confuse the script on the next iteration
Spath = 'C:\\Users\\okorn\\Documents\\2023 Aeromma\\INSTEP Plots\\'
#Create the full path with the figure name
savePath = os.path.join(Spath,'DC8_O3_tVOC_ratio')
#Save the figure to a filepath
fig.savefig(savePath)
