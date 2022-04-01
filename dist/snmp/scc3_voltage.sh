#!/bin/bash
if [ "$1" = "-g" ]
then
echo .1.3.6.1.2.1.25.1.15 #pv1 voltage
echo gauge
cat /home/pi/sundaya/dataLogging/mppt3_pv_voltage.txt
fi
exit 0
