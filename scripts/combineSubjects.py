"""
Combine the calibrationSummary.tsv files for all
conditions for all subjects
"""
from __future__ import print_function
from __future__ import division
import os
from os.path     import join
import pandas as pd

data_dir = '../data'
analysis_dir = '../analysis'

# loop through all subj/conditons
for subj in ['101', '102', '103']:
    for glasses in ['PupilLabs', 'SMI', 'Tobii']:
        for dist in ['1M', '2M', '3M']:
            for offset in ['0deg', '10Ldeg', '10Rdeg']:
                thisCond = '_'.join([subj, glasses, dist, offset])

                # load the calib summary for this condition
                calibSummary_path = join(data_dir, thisCond, 'calibration/calibrationSummary.tsv')
                calibSummary_df = pd.read_table(calibSummary_path, sep='\t')

                # add condition cols to the summmary
                calibSummary_df['subj'] = subj
                if glasses == 'PupilLabs':
                    model = 'Pupil Labs'        # reformat pupil labs to include space
                else:
                    model = glasses
                calibSummary_df['glasses'] = model
                calibSummary_df['dist'] = dist
                calibSummary_df['offset'] = offset

                # combine this file with the master
                if 'allSubjs_df' not in locals():
                    allSubjs_df = calibSummary_df.copy()
                else:
                    allSubjs_df = pd.concat([allSubjs_df, calibSummary_df])


# write the output
allSubjs_df.to_csv(join(analysis_dir, 'allSubjs_calibrationSummary.tsv'),
                    index=False,
                    sep='\t',
                    float_format='%.4f')
