"""Hand-Tracking: MediaPipe-Erkennung und Cursor-Informationen.

Dieses Modul enthält die `HandTracker`-Klasse, die ausschließlich die
Handerkennung durchführt und Cursor-/Pinch-Informationen bereitstellt.
Die Fenster- und UI-Steuerung wurde in `vision/anzeigefenster.py` ausgelagert.
"""

import mediapipe as mp
import math


class HandTracker:
    """Leichte Klasse, die MediaPipe initialisiert und pro Frame
    Cursor- und Pinch-Zustände liefert.

    Methoden:
    - process_frame(rgb_frame) -> dict: verarbeitet das RGB-Frame und
      gibt ein Dict mit keys `result`, `cursor`, `pinch_active`, `pinch_start`, `touching` zurück.
    - draw_cursor(screen, cursor, user_id): einfache Helfer, um Cursor auf ein Pygame-Surface
      zu zeichnen (optional, verwendet von Anzeige-Manager).
    """

    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height

        # MediaPipe Setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        # drawing utils (used by draw_landmarks)
        self.mp_draw = mp.solutions.drawing_utils

        # interne Zustände
        self.cursor_x = None
        self.cursor_y = None
        self.smoothing_factor = 0.7
        self.pinch_counter = 0
        self.pinch_threshold = 2
        self.last_pinch_active = False
        self.last_touching = False
        self.frame_counter = 0

    def process_frame(self, rgb_frame):
        """Verarbeitet ein RGB-Frame und bestimmt Cursor- und Pinch-Status.

        Rückgabe: dict mit Feldern:
          - result: MediaPipe-Ergebnisobjekt
          - cursor: (x,y) oder (None, None)
          - touching: bool (aktueller Abstand < Schwellwert)
          - pinch_active: bool (aktiver Pinch, nach Debounce)
          - pinch_start: bool (True in dem Frame, in dem Pinch erstmals aktiv wird)
        """
        result = self.hands.process(rgb_frame)
        self.frame_counter += 1

        pinch_active = False
        pinch_start = False
        touching = False

        if not result.multi_hand_landmarks:
            # reset smoothing when no hand
            self.cursor_x = None
            self.cursor_y = None
            self.pinch_counter = 0
            self.last_pinch_active = False
            return {
                "result": result,
                "cursor": (None, None),
                "touching": False,
                "pinch_active": False,
                "pinch_start": False,
            }

        for hand_lms in result.multi_hand_landmarks:
            thumb_tip = None
            index_tip = None

            for id, lm in enumerate(hand_lms.landmark):
                cx, cy = int(lm.x * self.width), int(lm.y * self.height)
                if id == 4:
                    thumb_tip = (cx, cy)
                if id == 8:
                    index_tip = (cx, cy)

            if thumb_tip and index_tip:
                thumb_x, thumb_y = thumb_tip
                if self.cursor_x is None:
                    self.cursor_x, self.cursor_y = thumb_x, thumb_y
                else:
                    self.cursor_x = int(
                        self.cursor_x * (1 - self.smoothing_factor) + thumb_x * self.smoothing_factor
                    )
                    self.cursor_y = int(
                        self.cursor_y * (1 - self.smoothing_factor) + thumb_y * self.smoothing_factor
                    )

                distance = math.hypot(index_tip[0] - thumb_tip[0], index_tip[1] - thumb_tip[1])
                touching = distance < 40

                if touching:
                    self.pinch_counter += 1
                else:
                    self.pinch_counter = 0

                pinch_active = self.pinch_counter >= self.pinch_threshold
                pinch_start = pinch_active and not self.last_pinch_active

                # update state for next frame
                self.last_pinch_active = pinch_active
                self.last_touching = touching

                return {
                    "result": result,
                    "cursor": (self.cursor_x, self.cursor_y),
                    "touching": touching,
                    "pinch_active": pinch_active,
                    "pinch_start": pinch_start,
                }

        # Fallback
        return {
            "result": result,
            "cursor": (None, None),
            "touching": False,
            "pinch_active": False,
            "pinch_start": False,
        }

    def draw_cursor(self, surface, cursor, user_id):
        """Zeichnet den Cursor auf das gegebene Pygame-Surface.

        Dieses Hilfsverfahren ist bewusst klein gehalten; komplexe UI-Aktionen
        bleiben Aufgabe von `anzeigefenster.py`.
        """
        try:
            import pygame
        except Exception:
            return

        if cursor is None or cursor[0] is None:
            return

        color = (0, 255, 255)
        if user_id == 1:
            color = (255, 0, 0)
        elif user_id == 2:
            color = (0, 255, 0)

        x, y = cursor
        if user_id == 1:
            pygame.draw.circle(surface, color, (x, y), 10)
        else:
            rect = pygame.Rect(x - 10, y - 10, 20, 20)
            pygame.draw.rect(surface, color, rect)

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

    # ---------------------------------------------------------
    # MediaPipe Landmarks zeichnen
    # ---------------------------------------------------------
    def draw_landmarks(self, rgb_frame, result):
        if result.multi_hand_landmarks:
            for hand_lms in result.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    rgb_frame,
                    hand_lms,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    self.mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2),
                )

    # ---------------------------------------------------------
    # Kamera-Bild anzeigen
    # ---------------------------------------------------------
    def draw_frame(self, rgb_frame):
        pass

    # ---------------------------------------------------------
    # Cursor zeichnen + Klicks + Logout-Trigger
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # FPS anzeigen
    # ---------------------------------------------------------
    # draw_fps removed from this lightweight tracker; UI/Anzeige verwaltet
    # rendering and font resources.

    # ---------------------------------------------------------
    # FPS anzeigen
    # ---------------------------------------------------------
    def draw_fps(self):
        counter_text = self.font.render(f"Frames: {self.frame_counter}", True, (255, 255, 255))
        text_width, text_height = counter_text.get_size()
        self.screen.blit(counter_text, (self.width - text_width - 20, self.height - text_height - 20))