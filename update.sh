#!/bin/bash

# Wechsel in das Git-Verzeichnis
cd /home/photo/PhotoBox/

# Git aktualisieren
git pull

FILE=/etc/systemd/system/PhotoBoxMaster.service
if test -f "$FILE"; then
    rm /etc/systemd/system/PhotoBoxMaster.service
    cp  /home/photo/PhotoBox/master/PhotoBoxMaster.service /etc/systemd/system/PhotoBoxMaster.service
    systemctl daemon-reload
    systemctl enable PhotoBoxMaster.service || /bin/true
fi

FILE=/etc/systemd/system/PhotoBoxKamera.service
if test -f "$FILE"; then
    rm /etc/systemd/system/PhotoBoxKamera.service
    cp  /home/photo/PhotoBox/kameras/PhotoBoxKamera.service /etc/systemd/system/PhotoBoxKamera.service
    systemctl daemon-reload
    systemctl enable PhotoBoxKamera.service || /bin/true
fi



