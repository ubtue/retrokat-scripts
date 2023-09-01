# Skripte für das RetroKat-Projekt

Ziel des Projekts ist die retrospektive Erschließung von Aufsatzdaten und ihr Nachweis im K10+.

Die Skripte haben ihre Ausgangsbasis in [helenanebel/Retrokat_Post_Processing](https://github.com/helenanebel/Retrokat_Post_Processing) und werden hier unter sich verändernden Rahmenbedingungen des Prozesses an der UB Tübingen weiterentwickelt.

## Benutzung

Für die Anwendung der Programme muss zusätzlich zum Download der Dateien ein Befehl ähnlich zu `make NAME={username}` ausgeführt werden, wobei `{username}` durch den korrekten Namen ersetzt werden muss.

Alternativ kann die Datei `personal_config_dummy.json` als `personal_config.json` gespeichert und die dortigen Angaben ergänzt werden.

## Workflow

Für die Generierung der Daten kann das Skript `commands_for_benu.py` genutzt werden, das die dafür nötigen Befehle darstellt. In jedem Fall sind weitere Konfigurationen nötig.

Für die Nachbearbeitung wird das Skript `post_process.py` benutzt. Falls weitere manuelle Nacharbeiten nötig sind, kann anschließend mithilfe von `merge_proper_and_post_process.py` eine finale Datei erzeugt werden.

Der Upload erfolgt mithilfe von `Rename files for FTP & move.py` bzw. `Move files to productive system.py`

