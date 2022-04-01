#!/bin/bash
if [ "$1" = "-g" ]
then
echo .1.3.6.1.2.1.25.1.24
echo gauge
cat /home/pi/sundaya/dataLogging/pln_voltage.txt
fi
exit 0
