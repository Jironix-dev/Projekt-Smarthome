from userinterface import SmartHomeUI
from vision.handtracking import HandTracker


if __name__ == "__main__":
    app = SmartHomeUI()
    app.run()
    tracker = HandTracker()
    tracker.run()

