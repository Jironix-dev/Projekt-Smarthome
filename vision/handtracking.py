import cv2
import mediapipe as mp
import pygame
import sys
import math

from vision.user_detection import UserDetector
from logsystem.logger import Logger
from ui.abmeldeknopf import LogoutButton


class HandTracker:
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height

        # -----------------------------
        # Pygame Setup
        # -----------------------------
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Handtracking – Klassenstruktur")
        self.font = pygame.font.SysFont("Arial", 30, bold=True)

        # -----------------------------
        # MediaPipe Setup
        # -----------------------------
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils

        # -----------------------------
        # Kamera Setup
        # -----------------------------
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(3, width)
        self.cap.set(4, height)

        # -----------------------------
        # Login / User Detection
        # -----------------------------
        self.user_detector = UserDetector()
        self.login_done = False
        self.user_id = None

        # Login-Steuerung
        self.login_allowed = True
        self.login_cooldown = 0
        self.pending_logout = False

        # -----------------------------
        # Logging
        # -----------------------------
        self.logger = Logger()
        self.last_touching = False

        # -----------------------------
        # Logout Button
        # -----------------------------
        self.logout_button = LogoutButton(x=20, y=20)

        # Frame Counter
        self.frame_counter = 0


    # ---------------------------------------------------------
    # Hauptschleife
    # ---------------------------------------------------------
    def run(self):
        while True:
            self.handle_events()

            # Kamera-Frame lesen
            success, frame = self.cap.read()
            if not success:
                continue

            # Login-Cooldown herunterzählen
            if self.login_cooldown > 0:
                self.login_cooldown -= 1

            # Bild spiegeln
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # MediaPipe verarbeiten
            result = self.hands.process(rgb_frame)

            # Prüfen, ob Hände im Bild sind
            hands_in_frame = bool(result.multi_hand_landmarks)

            # -------------------------------------------------
            # PENDING LOGOUT: Button wurde gedrückt,
            # Abmeldung erst, wenn Hand aus dem Bild ist
            # -------------------------------------------------
            if self.pending_logout and not hands_in_frame:
                self.logger.log(
                    user=f"User {self.user_id}",
                    action="Abmeldung durchgeführt"
                )

                self.login_done = False
                self.user_id = None
                self.pending_logout = False

                # Button zurücksetzen
                self.logout_button.reset()

                # Login erst wieder erlauben, wenn Timer abgelaufen ist
                self.login_allowed = False
                self.login_cooldown = 30  # ~1 Sekunde

            # -------------------------------------------------
            # LOGIN WIEDER ERLAUBEN, wenn:
            # - Timer abgelaufen
            # - Hand aus dem Bild
            # -------------------------------------------------
            if self.login_cooldown == 0 and not hands_in_frame:
                self.login_allowed = True

            # -------------------------------------------------
            # LOGIN-PHASE
            # -------------------------------------------------
            if not self.login_done and self.login_allowed and self.login_cooldown == 0:
                self.draw_frame(rgb_frame)

                login_text = self.font.render(
                    "Bitte Geste zeigen: Faust = User 1, Offene Hand = User 2",
                    True, (255, 255, 255)
                )
                self.screen.blit(login_text, (20, 20))

                user = self.user_detector.detect_user(rgb_frame)
                if user is not None:
                    self.user_id = user
                    self.login_done = True
                    self.login_allowed = False

                    # LOGIN LOGGEN
                    self.logger.log(
                        user=f"User {user}",
                        action="Anmeldung erfolgreich"
                    )

                pygame.display.flip()
                continue

            # -------------------------------------------------
            # NORMALES TRACKING
            # -------------------------------------------------
            self.frame_counter += 1

            self.draw_landmarks(rgb_frame, result)
            self.draw_frame(rgb_frame)

            # Logout Button anzeigen
            self.logout_button.draw(self.screen)

            # Cursor zeichnen
            self.draw_cursor(result)

            # FPS anzeigen
            self.draw_fps()

            pygame.display.flip()

        self.cap.release()
        pygame.quit()


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
                    self.mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2)
                )


    # ---------------------------------------------------------
    # Kamera-Bild anzeigen
    # ---------------------------------------------------------
    def draw_frame(self, rgb_frame):
        img_surface = pygame.image.frombuffer(
            rgb_frame.tobytes(),
            rgb_frame.shape[1::-1],
            "RGB"
        )
        self.screen.blit(img_surface, (0, 0))


    # ---------------------------------------------------------
    # Cursor zeichnen + Klicks + Logout-Trigger
    # ---------------------------------------------------------
    def draw_cursor(self, result):
        if not result.multi_hand_landmarks or self.user_id is None:
            return

        for hand_lms in result.multi_hand_landmarks:

            thumb_tip = None
            index_tip = None

            # Landmarks durchgehen
            for id, lm in enumerate(hand_lms.landmark):
                cx, cy = int(lm.x * self.width), int(lm.y * self.height)

                # Landmark Nummern anzeigen
                text = self.font.render(str(id), True, (255, 255, 0))
                self.screen.blit(text, (cx - 10, cy - 10))

                if id == 4:
                    thumb_tip = (cx, cy)
                if id == 8:
                    index_tip = (cx, cy)

            if thumb_tip and index_tip:

                # Abstand berechnen
                distance = math.hypot(
                    index_tip[0] - thumb_tip[0],
                    index_tip[1] - thumb_tip[1]
                )

                # Mittelpunkt
                mid_x = (thumb_tip[0] + index_tip[0]) // 2
                mid_y = (thumb_tip[1] + index_tip[1]) // 2

                # Pinch?
                touching = distance < 40

                # Farbe
                if touching:
                    color = (255, 0, 0)
                else:
                    color = (0, 255, 255) if self.user_id == 1 else (0, 255, 0)

                # -------------------------------------------------
                # LOGOUT-TRIGGER (Pinch + Button)
                # -------------------------------------------------
                if touching and not self.last_touching:
                    if self.logout_button.is_clicked(mid_x, mid_y):
                        self.pending_logout = True
                        self.login_allowed = False
                        self.logout_button.set_pressed()

                # -------------------------------------------------
                # NORMALER LINKSKLICK LOG (nur einmal)
                # -------------------------------------------------
                if touching and not self.last_touching and not self.pending_logout:
                    self.logger.log(
                        user=f"User {self.user_id}",
                        action="Linksklick ausgeführt"
                    )

                # Zustand speichern
                self.last_touching = touching

                # -------------------------------------------------
                # CURSOR ZEICHNEN
                # -------------------------------------------------
                if self.user_id == 1:
                    pygame.draw.circle(self.screen, color, (mid_x, mid_y), 10)

                elif self.user_id == 2:
                    rect = pygame.Rect(mid_x - 10, mid_y - 10, 20, 20)
                    pygame.draw.rect(self.screen, color, rect)


    # ---------------------------------------------------------
    # FPS anzeigen
    # ---------------------------------------------------------
    def draw_fps(self):
        counter_text = self.font.render(
            f"Frames: {self.frame_counter}",
            True, (255, 255, 255)
        )
        text_width, text_height = counter_text.get_size()
        self.screen.blit(
            counter_text,
            (self.width - text_width - 20, self.height - text_height - 20)
        )