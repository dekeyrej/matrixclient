#!/bin/bash
export PROD=1
export DIR="/home/pi/matrixclient"
cd $DIR
source venv/bin/activate
$DIR/venv/bin/python $DIR/clientdisplay.py -i 1
