#Name: Kevin Dietrich, Kevin Wesner
#Datum: 26.01.2026
#Projekt: Smart-Home

from ui.userinterface import SmartHomeUI
from vision.handtracking import HandTracker
import threading

if __name__ == "__main__":
    # -------- 1. UI erstellen --------
    app = SmartHomeUI()

    # -------- 2. HandTracker erstellen --------
    tracker = HandTracker(width=app.WIDTH, height=app.HEIGHT, ui=app)

    # -------- 3. HandTracker in Hauptthread starten --------
    # The main run loop handles both hand tracking and UI display
    tracker.run()

