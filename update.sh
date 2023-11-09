#!/bin/bash

# Wechsel in das Git-Verzeichnis
cd /home/photo/PhotoBox/

# Git aktualisieren
git pull

rm /etc/systemd/system/PhotoBoxUpdate.service
cp  /home/photo/PhotoBox/PhotoBoxUpdate.service /etc/systemd/system/PhotoBoxUpdate.service
systemctl daemon-reload
systemctl enable PhotoBoxUpdate.service || /bin/true

FILE=/etc/systemd/system/PhotoBoxMaster.service
if test -f "$FILE"; then
    rm /etc/systemd/system/PhotoBoxMaster.service
    cp  /home/photo/PhotoBox/master/PhotoBoxMaster.service /etc/systemd/system/PhotoBoxMaster.service
    systemctl daemon-reload
    systemctl enable PhotoBoxMaster.service || /bin/true
    systemctl restart PhotoBoxMaster.service || /bin/true
fi

FILE=/etc/systemd/system/PhotoBoxMaster.service
if test -f "$FILE"; then
    rm /etc/systemd/system/PhotoBoxKamera.service
    cp  /home/photo/PhotoBox/kameras/PhotoBoxKamera.service /etc/systemd/system/PhotoBoxKamera.service
    systemctl daemon-reload
    systemctl restart PhotoBoxKamera.service || /bin/true
fi



