#!/bin/sh
conda create -y --name gitquality python=3
conda install -y -n gitquality --file requirements.txt
source activate gitquality
pip install -r requirements-pip.txt
