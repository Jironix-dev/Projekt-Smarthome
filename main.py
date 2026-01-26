# Name: Kevin Dietrich, Kevin Wesner
# Datum: 26.01.2026
# Projekt: Smart-Home

"""Startpunkt des Smart-Home Programms.

Dieses Modul erstellt die UI-Instanz und den HandTracker und startet die
Hauptschleife. Es ist der Einstiegspunkt (`__main__`).
"""

from ui.userinterface import SmartHomeUI
from vision.handtracking import HandTracker
import threading


if __name__ == "__main__":
    # UI erstellen
    app = SmartHomeUI()

    # HandTracker erstellen und mit der UI verbinden
    tracker = HandTracker(width=app.WIDTH, height=app.HEIGHT, ui=app)

    # Hauptschleife starten (HandTracker führt das Rendering und Tracking)
    tracker.run()

