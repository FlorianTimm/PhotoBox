#!/bin/bash

echo -n "install (1) Kamera or (2) Master : "
read n
 
if [ $n -eq 1 ]
then
  cp  /home/photo/PhotoBox/kameras/PhotoBoxKamera.service /etc/systemd/system/PhotoBoxKamera.service
fi

if [ $n -eq 2 ]
then
  cp  /home/photo/PhotoBox/master/PhotoBoxMaster.service /etc/systemd/system/PhotoBoxMaster.service
fi