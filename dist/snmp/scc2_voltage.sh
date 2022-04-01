#!/bin/bash
if [ "$1" = "-g" ]
then
echo .1.3.6.1.2.1.25.1.13 #pv2 voltage
echo gauge
cat /home/pi/sundaya/dataLogging/mppt2_pv_voltage.txt
fi
exit 0

