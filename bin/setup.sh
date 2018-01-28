#!/bin/sh
conda create --name gitquality python=3
source activate gitquality
conda install --file requirements.txt
pip install -r requirements-pip.txt
