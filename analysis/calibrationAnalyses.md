Wearable Eye-tracker Calibration Analyses
=========================================

A set of analyses comparing calibration performance across 3 different
models of wearable eye-trackers: Tobii Glasses 2, SMI, and Pupil Labs.
Each tracker was tested on 3 different subjects. Each subject performed
calibration tasks at 3 different distances (1M, 2M, and 3M). At each
distance, calibration was tested at 3 different conditons of visual
angle offset (-10deg, 0deg, +10deg). The calibration task consisted of
asking participants to fixate on a sequence of 9 calibration points (3 x
3 grid) presented in a random order for 3 seconds each. The analysis
focuses on the gaze data collected between 500ms and 2500ms on each
point.

Read in processed calibration data file
---------------------------------------

Each row represents the calibration performance summary for one pt (of
9) for one conditon for one subject.

    library(readr)
    library(knitr)

    calibData <- read_delim("allSubjs_calibrationSummary.tsv", delim="\t")
    kable(calibData[1:5,], caption='Calibration Data, all subjects')

<table>
<caption>Calibration Data, all subjects</caption>
<thead>
<tr class="header">
<th align="right">trial</th>
<th align="right">ptIdx</th>
<th align="right">percentValid</th>
<th align="right">centX</th>
<th align="right">centY</th>
<th align="right">centDist</th>
<th align="right">centAngle</th>
<th align="right">RMS</th>
<th align="right">subj</th>
<th align="left">glasses</th>
<th align="left">dist</th>
<th align="left">offset</th>
<th align="left">condition</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="right">1</td>
<td align="right">15</td>
<td align="right">0.992</td>
<td align="right">872.513</td>
<td align="right">456.424</td>
<td align="right">0.683</td>
<td align="right">48.041</td>
<td align="right">0.113</td>
<td align="right">101</td>
<td align="left">Pupil Labs</td>
<td align="left">1M</td>
<td align="left">0deg</td>
<td align="left">101_PupilLabs_1M_0deg</td>
</tr>
<tr class="even">
<td align="right">2</td>
<td align="right">21</td>
<td align="right">0.996</td>
<td align="right">178.414</td>
<td align="right">736.665</td>
<td align="right">1.135</td>
<td align="right">83.071</td>
<td align="right">0.074</td>
<td align="right">101</td>
<td align="left">Pupil Labs</td>
<td align="left">1M</td>
<td align="left">0deg</td>
<td align="left">101_PupilLabs_1M_0deg</td>
</tr>
<tr class="odd">
<td align="right">3</td>
<td align="right">3</td>
<td align="right">0.992</td>
<td align="right">529.483</td>
<td align="right">128.252</td>
<td align="right">0.564</td>
<td align="right">52.494</td>
<td align="right">0.114</td>
<td align="right">101</td>
<td align="left">Pupil Labs</td>
<td align="left">1M</td>
<td align="left">0deg</td>
<td align="left">101_PupilLabs_1M_0deg</td>
</tr>
<tr class="even">
<td align="right">4</td>
<td align="right">13</td>
<td align="right">0.988</td>
<td align="right">537.017</td>
<td align="right">401.570</td>
<td align="right">1.226</td>
<td align="right">69.390</td>
<td align="right">0.123</td>
<td align="right">101</td>
<td align="left">Pupil Labs</td>
<td align="left">1M</td>
<td align="left">0deg</td>
<td align="left">101_PupilLabs_1M_0deg</td>
</tr>
<tr class="odd">
<td align="right">5</td>
<td align="right">25</td>
<td align="right">0.992</td>
<td align="right">862.071</td>
<td align="right">709.513</td>
<td align="right">1.481</td>
<td align="right">76.933</td>
<td align="right">0.087</td>
<td align="right">101</td>
<td align="left">Pupil Labs</td>
<td align="left">1M</td>
<td align="left">0deg</td>
<td align="left">101_PupilLabs_1M_0deg</td>
</tr>
</tbody>
</table>

Average by condition
--------------------

Each condition (i.e. calibration task at a given distance and given
offset) contained 9 distinct calibration points. As a first step,
average calibration performance across all 9 pts for each condition.

    print("test")

    ## [1] "test"

You can also embed plots, for example:

![](calibrationAnalyses_files/figure-markdown_strict/pressure-1.png)

Note that the `echo = FALSE` parameter was added to the code chunk to
prevent printing of the R code that generated the plot.
