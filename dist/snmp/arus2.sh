#!/bin/bash
if [ "$1" = "-g" ]
then
echo .1.3.6.1.2.1.25.1.18 #arus2
echo gauge
cat /home/pi/sundaya/dataLogging/arus2.txt
fi
exit 0
