#!/bin/bash

# Wechsel in das Git-Verzeichnis
cd /home/photo/PhotoBox/
git config --global --add safe.directory /home/photo/PhotoBox
sudo git config --global --add safe.directory /home/photo/PhotoBox


# Git aktualisieren
sudo git -C /home/photo/PhotoBox pull

FILE=/etc/systemd/system/PhotoBoxMaster.service
if test -f "$FILE"; then
    rm /etc/systemd/system/PhotoBoxMaster.service
    cp  /home/photo/PhotoBox/master/PhotoBoxMaster.service /etc/systemd/system/PhotoBoxMaster.service
    systemctl daemon-reload
    systemctl enable PhotoBoxMaster.service || /bin/true
fi

FILE=/etc/systemd/system/PhotoBoxCamera.service
if test -f "$FILE"; then
    rm /etc/systemd/system/PhotoBoxCamera.service
    cp  /home/photo/PhotoBox/camera/PhotoBoxCamera.service /etc/systemd/system/PhotoBoxCamera.service
    systemctl daemon-reload
    systemctl enable PhotoBoxCamera.service || /bin/true
fi



