#!/bin/sh
conda create --name gitquality python=3
conda install -n gitquality --file requirements.txt
source activate gitquality
pip install -r requirements-pip.txt
