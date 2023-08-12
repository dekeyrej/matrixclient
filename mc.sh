#!/bin/bash
# export MONGO_HOST=rocket3
cd /home/pi/kubematrix/client
source bin/activate
#/snap/bin/kubectl port-forward -n cockroach-operator-system service/cockroachdb-public 26257:26257 &
/home/pi/kubematrix/client/clientdisplay.py -i 1
#/home/pi/matrix/clientdisplay.py
