#!/bin/bash

# Wechsel in das Git-Verzeichnis
cd /home/photo/PhotoBox/

# Git aktualisieren
git pull

cp  /home/photo/PhotoBox/PhotoBoxMaster.service /etc/systemd/system/PhotoBoxMaster.service
cp  /home/photo/PhotoBox/PhotoBoxKamera.service /etc/systemd/system/PhotoBoxKamera.service
systemctl daemon-reload

# Service neu starten
systemctl restart PhotoBoxMaster.service || /bin/true
systemctl restart PhotoBoxKamera.service || /bin/true


