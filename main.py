# Name: Kevin Dietrich, Kevin Wesner
# Datum: 26.01.2026
# Projekt: Smart-Home

"""Startpunkt des Smart-Home Programms.

Dieses Modul erstellt die UI-Instanz und den HandTracker und startet die
Hauptschleife. Es ist der Einstiegspunkt (`__main__`).
"""

from vision.anzeigefenster import AnzeigeFenster

if __name__ == "__main__":
    # Anzeige-Fenster (erstellt UI intern) und starten
    window = AnzeigeFenster()
    window.run()