#!/bin/bash
if [ "$1" = "-g" ]
then
echo .1.3.6.1.2.1.25.1.40
echo gauge
cat /home/pi/sundaya/dataLogging/current_load.txt
fi
exit 0
