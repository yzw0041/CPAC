#!/usr/bin/env python3
import argparse
import os
import nibabel
import numpy
from glob import glob
from subprocess import Popen, PIPE
from shutil import rmtree
import subprocess

def run(command, env={}):
    process = Popen(command, stdout=PIPE, stderr=subprocess.STDOUT,
        shell=True, env=env)
    while True:
        line = process.stdout.readline()
        line = str(line, 'utf-8')[:-1]
        print(line)
        if line == '' and process.poll() != None:
            break

parser = argparse.ArgumentParser(
    description='C-PAC Pipeline Runner')
parser.add_argument('bids_dir', help='The directory with the input dataset '
    'formatted according to the BIDS standard.')
parser.add_argument('output_dir', help='The directory where the output files '
    'should be stored. If you are running group level analysis '
    'this folder should be prepopulated with the results of the'
    'participant level analysis.')
parser.add_argument('analysis_level', help='Level of the analysis that will '
    ' be performed. Multiple participant level analyses can be run '
    ' independently (in parallel) using the same output_dir.',
    choices=['participant', 'group'])
parser.add_argument('--participant_label', help='The label of the participant'
    ' that should be analyzed. The label '
    'corresponds to sub-<participant_label> from the BIDS spec '
    '(so it does not include "sub-"). If this parameter is not '
    'provided all subjects should be analyzed. Multiple '
    'participants can be specified with a space separated list.',
    nargs="+")
parser.add_argument('--template_name', help='Name for the custom group level '
    ' template generated for this dataset', default="newtemplate")

args = parser.parse_args()

subjects_to_analyze = []
# only for a subset of subjects
if args.participant_label:
    subjects_to_analyze = args.participant_label
# for all subjects
else:
    subject_dirs = glob(os.path.join(args.bids_dir, "sub-*"))
    subjects_to_analyze = \
        [subject_dir.split("-")[-1] for subject_dir in subject_dirs]

# running participant level
if args.analysis_level == "participant":
    # find all T1s and skullstrip them
    for subject_label in subjects_to_analyze:
        # grab all T1s from all sessions
        input_args = " ".join(["-i %s"%f for f in \
            glob(os.path.join(args.bids_dir,"sub-%s"%subject_label,"anat",
                "*_T1w.nii*")) + \
            glob(os.path.join(args.bids_dir,"sub-%s"%subject_label,"ses-*",
                "anat", "*_T1w.nii*"))])
        cmd = "echo 'CPAC participant analysis: %s %s %s'"%(subject_label,
            args.output_dir, input_args)
        print(cmd)
        if os.path.exists(os.path.join(args.output_dir, subject_label)):
            rmtree(os.path.join(args.output_dir, subject_label))
        run(cmd)
elif args.analysis_level == "group":
    # running group level
    # generate study specific template
    cmd = "echo 'CPAC group analysis " +  " ".join(subjects_to_analyze) + "'"
    print(cmd)
    run(cmd, env={"SUBJECTS_DIR": args.output_dir})
