%CH4 post-processing script
load('YPODR9_hybrid_field_estimate.mat')
load('YPODR9_field_t.mat')

%Step 1: Calibrate the data using the hybrid approach:
      %1a) Fit a linear regression on the data
      %1b) Calculate the residuals for colocation
      %1c) Fit a random forest to the residuals (python)
      %1d) Add the linreg & rf outputs together as new estimate

%Step 2:Apply smoothing (movmedian)
smoothed = movmedian(hybrid_field,15); %to preserve spikes but reduce noise
%Step 3: Fit a line to the smoothed, calibrated data (piecewise if gaps)
dates=datenum(xt);
mdl = fitlm(dates, smoothed);
line = predict(mdl, dates);
%Step 4: Subtract out the line
corrected1 = smoothed - line;
%Step 5: Add back in the megacities mean atmosperhic background 
final = corrected1 + 2.1;

%Save out the results on their own
save('myData.mat', 'final')
%Also save as a csv for future use
field_corrected=timetable(xt,final);
writetimetable(field_corrected,'YPODR9_field_corrected.csv')




