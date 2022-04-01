#!/bin/bash
if [ "$1" = "-g" ]
then
echo .1.3.6.1.2.1.25.1.39
echo gauge
cat /home/pi/sundaya/dataLogging/voltage_load.txt
fi
exit 0
