# glassesCalibration
calibration tests for wearable eye-tracking glasses

---
Testing calibration accuracy and precision across 3 different models of wearable trackers

* Tobii Glasses 2
* Pupil Labs
* SMI

The data and model-specific analysis scripts for each manufacturer are found in their respective directories in the root folder. 


## Task
Subjects seated facing the calibratrion grid at a distance of 1402mm. With this 25pt calibration grid (see `referenceGrids/calibrationGrid.pdf`), from a distance of 1402mm, each point is separated by 1deg of visual angle. 

Subjects will perform 7 different calibration tests that vary according to the angle of horizontal offset of the center calibration point relative to the subject's head position (the 0deg offset condition corresponds to when the calibration grid is placed on the wall directly facing the subject). The conditions are:

* 15deg left
* 10deg left
* 5deg left
* 0deg
* 5deg right
* 10deg right
* 15deg right

Left/Right are relative to the subject's field of view. 

In each condition, the subject will be asked to fixate on 9 different calibration points presented in the grid. The calibration grid itself is a 25pt (5x5) grid; the 9 calibration points will correspond to the 4 outer corners, the 4 midpoints of each outer edge, and the center point (i.e. 3x3 grid). 

The order of calibration points will be randomly determined on each calibration. Each calibration point will indicated to the participant by "spoken" instruction (generated from system speech tools) indicating the column, row number of the point to fixate on. Subjects will be asked to fixate on each point for 3 seconds

## Analysis
