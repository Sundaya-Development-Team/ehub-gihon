#!/bin/bash
if [ "$1" = "-g" ]
then
echo .1.3.6.1.2.1.25.1.21 #batt2 voltage
echo gauge
cat /home/pi/sundaya/dataLogging/pln_voltage.txt
fi
exit 0

