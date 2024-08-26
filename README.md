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