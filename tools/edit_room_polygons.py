# Name: Kevin Dietrich
# Datum: 27.01.2026
# Projekt: Smarthome Steuerung

"""Interaktiver Polygon-Editor für Raum-Zonen.

Verwendung:
    python tools/edit_room_polygons.py

Beschreibung:
- Lädt `Bilder/grundriss_neu.png` und zeigt es an.
- Für jeden Raum (Badezimmer, Schlafzimmer, Wohnzimmer, Kueche) können
  Punkte per Mausklick gesetzt werden, um ein Polygon zu definieren.
- Drücke ENTER, um das aktuelle Polygon abzuschließen, BACKSPACE um den
  letzten Punkt zu löschen.
- Drücke 'n' um zum nächsten Raum zu wechseln, 's' um zu speichern und zu beenden.
- Die Polygone werden in `tools/room_polygons.json` im normalisierten
  Format (0..1 relativ zur Bildgröße) gespeichert.
"""

import os
import json
import cv2
import numpy as np


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_PATH = os.path.join(ROOT, "Bilder", "grundriss_neu.png")
OUT_PATH = os.path.join(ROOT, "tools", "room_polygons.json")

ROOMS = ["Badezimmer", "Schlafzimmer", "Wohnzimmer", "Kueche"]

img = cv2.imread(IMG_PATH)
if img is None:
    print("Cannot load", IMG_PATH)
    raise SystemExit(1)

h, w = img.shape[:2]

polygons = {}
win = "Polygone editieren - Enter finish, s save, n next, Backspace undo"
cv2.namedWindow(win, cv2.WINDOW_NORMAL)
cv2.imshow(win, img)

current = []
room_idx = 0


def draw_preview():
    disp = img.copy()
    # draw existing polygons
    for r, pts in polygons.items():
        pts_px = [(int(x * w), int(y * h)) for (x, y) in pts]
        if len(pts_px) >= 3:
            cv2.polylines(disp, [np.array(pts_px)], True, (0, 255, 255), 2)
    # draw current
    if current:
        for i in range(len(current) - 1):
            cv2.line(disp, current[i], current[i + 1], (0, 255, 0), 2)
        for p in current:
            cv2.circle(disp, p, 4, (0, 0, 255), -1)
    cv2.putText(
        disp,
        f"Room: {ROOMS[room_idx]}  Points: {len(current)}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
    )
    cv2.imshow(win, disp)


def on_mouse(event, x, y, flags, param):
    global current
    if event == cv2.EVENT_LBUTTONDOWN:
        current.append((x, y))
        draw_preview()


cv2.setMouseCallback(win, on_mouse)

draw_preview()
print(
    "Instructions: click to add points, ENTER to finish polygon, BACKSPACE to undo, n to next room, s to save+exit"
)
while True:
    key = cv2.waitKey(0) & 0xFF
    if key == 13:  # Enter -> finish polygon
        if len(current) >= 3:
            # normalize
            norm = [(p[0] / w, p[1] / h) for p in current]
            polygons[ROOMS[room_idx]] = norm
            print(f"Saved polygon for {ROOMS[room_idx]} ({len(norm)} points)")
            current = []
        else:
            print("Need at least 3 points to finish polygon")
        draw_preview()
    elif key == 8:  # Backspace
        if current:
            current.pop()
        draw_preview()
    elif key == ord("n"):
        # skip to next room
        current = []
        room_idx = min(room_idx + 1, len(ROOMS) - 1)
        draw_preview()
    elif key == ord("s"):
        # save and exit
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(polygons, f, indent=2)
        print("Saved", OUT_PATH)
        break
    elif key == 27:  # ESC
        print("Aborted, no changes saved")
        break

cv2.destroyAllWindows()
