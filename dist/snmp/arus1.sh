#!/bin/bash
if [ "$1" = "-g" ]
then
echo .1.3.6.1.2.1.25.1.17 #arus1
echo gauge
cat /home/pi/sundaya/dataLogging/arus1.txt
fi
exit 0
