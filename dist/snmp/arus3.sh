#!/bin/bash
if [ "$1" = "-g" ]
then
echo .1.3.6.1.2.1.25.1.24 #arus3
echo gauge
cat /home/pi/sundaya/dataLogging/arus3.txt
fi
exit 0
