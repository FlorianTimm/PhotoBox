# PhotoBox

Es handelt sich bei diesem Projekt um eine Masterthesis im Studiengang Geodäsie und Geoinformatik an der HafenCity Universität Hamburg. Dieses Repository enthält den Quellcode hierzu. Die Dokumentation in Form der Thesis befindet sich im Repository [https://github.com/FlorianTimm/PhotoBox_Thesis].

## Ordnerstruktur

* master - Python-Script für den steuernden Raspberry Pi 4
* camera - Python-Script für die einzelnen Raspberry Pi Zero W mit angeschlossenem Kameramodul v3
* common - von master und camera genutzter Quellcode
* connector - Java-Programm zum Herstellen einer Verbindung zu NodeODM
* doc - UML-Diagramme und weitere Quelltext-Doku
* template - von master und camera genutzte HTML-Templates
* test - PyTest-Tests für master, camera und common

## Installation auf Raspberry Pi

### Notwendige Pakete installieren
```
sudo apt install git python3-flask python3-flask-cors python3-opencv --no-install-recommends
```

#### zusätzlich als Kamera-Steuerung
```
sudo apt install python3-picamera2 --no-install-recommends
```

### Code laden und installieren
```
git clone https://github.com/FlorianTimm/PhotoBox.git
cd PhotoBox
sudo ./install.sh
```

## Ausführung der Desktop-Software
Die ausführbare jar-Datei muss im gleichen Ordner liegen wie die Java-API-Dateien von Metashape und die entsprechende Lizenz-Datei, sofern Metashape genutzt werden soll. Ansonsten ist ein installiertes oder portables Java-Runtime-Environment notwendig.
