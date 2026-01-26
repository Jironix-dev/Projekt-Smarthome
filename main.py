from ui.userinterface import SmartHomeUI
from vision.handtracking import HandTracker
import threading


if __name__ == "__main__":
    # -------- 1. UI erstellen --------
    app = SmartHomeUI()

    # -------- 2. HandTracker erstellen --------
    tracker = HandTracker(ui=app)
    tracker.ui = app  # HandTracker weiß, welche UI gesteuert wird

    # -------- 3. HandTracker in separatem Thread starten --------
    tracker_thread = threading.Thread(target=tracker.run, daemon=True)
    tracker_thread.start()

    # -------- 4. UI-Loop starten --------
    # Dieser Thread zeigt die Oberfläche, zeichnet alles
    app.run()

