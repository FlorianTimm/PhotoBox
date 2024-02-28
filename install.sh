#!/bin/bash

echo -n "install (1) Camera or (2) Master : "
read n
 
if [ $n -eq 1 ]
then
  cp  /home/photo/PhotoBox/camera/PhotoBoxKamera.service /etc/systemd/system/PhotoBoxCamera.service
fi

if [ $n -eq 2 ]
then
  cp  /home/photo/PhotoBox/master/PhotoBoxMaster.service /etc/systemd/system/PhotoBoxMaster.service
fi

./update.sh