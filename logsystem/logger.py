import csv
import os
from datetime import datetime


class Logger:
    def __init__(self):
        # Pfad zur CSV-Datei im selben Ordner wie logger.py
        self.file_path = os.path.join(os.path.dirname(__file__), "activity_log.csv")

        # Falls Datei noch nicht existiert → Kopfzeile schreiben
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file, delimiter="|")
                writer.writerow(["Datum", "Uhrzeit", "Nutzer", "Aktion"])

    def log(self, user, action):
        """Speichert eine Aktivität in der CSV-Datei."""
        now = datetime.now()
        date = now.strftime("%d.%m.%Y")
        time = now.strftime("%H:%M:%S")

        with open(self.file_path, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter="|")
            writer.writerow([date, time, user, action])