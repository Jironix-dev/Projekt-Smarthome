#Name: Kevin Dietrich, Kevin Wesner
#Datum: 26.01.2026
#Projekt: Smart-Home

import cv2
import mediapipe as mp
import pygame
import sys
import math

from vision.user_detection import UserDetector
from vision.kamera_anzeige import KameraAnzeige
from logsystem.logger import Logger
from ui.abmeldeknopf import LogoutButton
from ui.knopf_beenden import ExitButton
from ui.menu_knopf import MenuButton


class HandTracker:
    def __init__(self, width=1280, height=720, ui=None):
        self.ui = ui
        self.width = width
        self.height = height

        # -----------------------------
        # Pygame Setup (single window for both tracking and UI)
        # -----------------------------
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Handtracking – Klassenstruktur")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 30, bold=True)
        
        # Update UI screen reference to use this single screen
        if self.ui:
            self.ui.screen = self.screen
            # Verwende die Buttons von der UI statt eigene zu erstellen
            self.menu_button = self.ui.menu_button
            self.logout_button = self.ui.logout_button
            self.exit_button = self.ui.exit_button
        else:
            # Fallback: Erstelle Buttons, wenn keine UI vorhanden ist
            self.menu_button = MenuButton(x=80, y=20)
            self.logout_button = LogoutButton(x=80, y=90)
            self.exit_button = ExitButton(x=80, y=160)

        # -----------------------------
        # MediaPipe Setup
        # -----------------------------
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,  # Nur eine Hand tracken für bessere Performance
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils

        # -----------------------------
        # Kamera Setup
        # -----------------------------
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(3, width)
        self.cap.set(4, height)
        # Performance-Optimierungen
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer auf 1 Frame limitieren
        self.cap.set(cv2.CAP_PROP_FPS, 30)  # FPS auf 30 setzen

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


        #Cursorpostiion speichern
        self.cursor_x = None
        self.cursor_y = None
        self.smoothing_factor = 0.7  # Höher = schneller folgen (70% neue Position, 30% alte)
        self.pinch_counter = 0
        self.pinch_threshold = 2

        # Frame Counter
        self.frame_counter = 0
        
        # Pinch state tracking (prevent repeated actions)
        self.last_pinch_active = False
        
        # Kamera-Anzeige initialisieren
        self.kamera_anzeige = KameraAnzeige(width, height)


    # ---------------------------------------------------------
    # Hauptschleife
    # ---------------------------------------------------------
    def run(self):
        while True:
            self.clock.tick(60)  # 60 FPS - schneller ist auf den meisten Systemen nicht nötig

            # Kamera-Frame lesen
            success, frame = self.cap.read()
            if not success:
                continue

            # Login-Cooldown herunterzählen
            if self.login_cooldown > 0:
                self.login_cooldown -= 1

            # Bild spiegeln
            frame = cv2.flip(frame, 1)
            # RGB-Konvertierung optimiert
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
                
                # Menü schließen
                if self.menu_button.is_open:
                    self.menu_button.toggle()

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
                # Clear screen - only show login message
                self.screen.fill((0, 0, 0))

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
                    
                    # Reset logout button on successful login
                    if self.ui:
                        self.ui.logout_button.reset()
                    else:
                        self.logout_button.reset()

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

            # Clear screen once
            self.screen.fill((0, 0, 0))
            
            # Draw UI based on current view
            if self.ui:
                if self.ui.current_view == "HOME":
                    # HOME VIEW
                    self.ui.draw_gradient(self.screen, (20, 25, 40), (10, 10, 10))
                    self.screen.blit(self.ui.floorplan, self.ui.floorplan_pos)
                    
                    # Draw overlay if room is selected (nur wenn Menü nicht offen ist)
                    if self.ui.selected_room and not self.menu_button.is_open:
                        self.ui.draw_focus_overlay(self.ui.room_zones[self.ui.selected_room])
                    
                    # Draw all rooms (nur wenn Menü nicht offen ist)
                    if not self.menu_button.is_open:
                        for room, rect in self.ui.room_zones.items():
                            if room != self.ui.selected_room:
                                self.ui.draw_room(room, rect, self.ui.rooms[room], False)
                
                elif self.ui.current_view == "SCHLAFZIMMER":
                    # SCHLAFZIMMER VIEW
                    self.ui.schlafzimmer_view.draw()
            
            # Landmarks-Visualisierung deaktiviert für bessere Performance
            # (nicht notwendig für Funktionalität)
            # self.draw_landmarks(rgb_frame, result)
            self.draw_frame(rgb_frame)
            
            # Menu Overlay zeichnen (wenn Menü offen) - in allen Views
            if self.ui and self.menu_button.is_open:
                self.menu_button.draw_overlay(self.screen, self.width, self.height)
            
            # Menü-Knopf und Buttons nur in HOME-View anzeigen (werden von Views in anderen Screens gezeichnet)
            if self.ui and self.ui.current_view == "HOME":
                # Menü-Knopf nur in HOME-View anzeigen
                self.menu_button.draw(self.screen)

                # Logout und Exit Buttons nur anzeigen, wenn Menü offen ist
                if self.menu_button.is_open:
                    self.logout_button.draw(self.screen)
                    self.logout_button.update() if hasattr(self.logout_button, 'update') else None
                    
                    self.exit_button.draw(self.screen)
                    self.exit_button.update()
            
            # In SCHLAFZIMMER-View: Logout und Exit Buttons zeichnen, wenn Menü offen
            elif self.ui and self.ui.current_view == "SCHLAFZIMMER" and self.menu_button.is_open:
                self.logout_button.draw(self.screen)
                self.logout_button.update() if hasattr(self.logout_button, 'update') else None
                
                self.exit_button.draw(self.screen)
                self.exit_button.update()

            # Cursor zeichnen
            self.draw_cursor(result)

            # Kamera-Feed in der unteren rechten Ecke anzeigen (wenn aktiviert)
            self.kamera_anzeige.draw_camera_feed(self.screen, rgb_frame)

            # FPS anzeigen
            #self.draw_fps()

            # Single display update per frame
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
        pass


    # ---------------------------------------------------------
    # Cursor zeichnen + Klicks + Logout-Trigger
    # ---------------------------------------------------------
    def draw_cursor(self, result):
        pinch_active = False

        if not result.multi_hand_landmarks or self.ui is None:
            return

        for hand_lms in result.multi_hand_landmarks:

            thumb_tip = None
            index_tip = None

            # Landmarks durchgehen
            for id, lm in enumerate(hand_lms.landmark):
                cx, cy = int(lm.x * self.width), int(lm.y * self.height)

                if id == 4:
                    thumb_tip = (cx, cy)
                if id == 8:
                    index_tip = (cx, cy)

            if thumb_tip and index_tip:

                # Cursor auf Daumenspitze positionieren
                thumb_x = thumb_tip[0]
                thumb_y = thumb_tip[1]

                if self.cursor_x is None:
                    self.cursor_x = thumb_x
                    self.cursor_y = thumb_y
                else:
                    self.cursor_x = int(self.cursor_x * (1 - self.smoothing_factor) + thumb_x * self.smoothing_factor)
                    self.cursor_y = int(self.cursor_y * (1 - self.smoothing_factor) + thumb_y * self.smoothing_factor)
                
                cursor_pos = (self.cursor_x, self.cursor_y)

                distance = math.hypot(
                    index_tip[0] - thumb_tip[0],
                    index_tip[1] - thumb_tip[1]
                )
                # Pinch?
                touching = distance < 40

                # Farbe definieren (wird später für Cursor-Zeichnung benötigt)
                if touching:
                    color = (255, 0, 0)
                else:
                    color = (0, 255, 255) if self.user_id == 1 else (0, 255, 0)

                # Neues Flag für einmalige Auslösung pro Pinch
                if pinch_active and not self.last_pinch_active:
                    self.on_pinch(self.cursor_x, self.cursor_y)

                if touching: 
                    self.pinch_counter += 1
                else:
                    self.pinch_counter = 0
                
                pinch_active = self.pinch_counter >= self.pinch_threshold
                
                #Räume auf UI über Pinch (only trigger once per pinch)
                if pinch_active and not self.last_pinch_active:
                    # Wenn Menü offen ist: Nur Menü-Buttons verarbeiten
                    if self.menu_button.is_open:
                        # Zurück-Button in Schlafzimmer-View
                        if self.ui and self.ui.current_view == "SCHLAFZIMMER":
                            if self.ui.schlafzimmer_view.back_button.is_clicked(*cursor_pos):
                                # Zurück-Button in Schlafzimmer-View ist nicht sichtbar wenn Menü offen
                                pass
                        
                        # Menu Button Toggle
                        if self.menu_button.is_clicked(*cursor_pos):
                            self.menu_button.toggle()
                            # Logging für Menü
                            menu_state = "geöffnet" if self.menu_button.is_open else "geschlossen"
                            self.logger.log(
                                user=f"User {self.user_id}",
                                action=f"Menü wurde {menu_state}"
                            )
                        
                        # LOGOUT-TRIGGER (Pinch + Button)
                        elif self.logout_button.is_clicked(*cursor_pos):
                            self.pending_logout = True
                            self.login_allowed = False
                            self.logout_button.set_pressed()
                            # Logging für Abmeldeknopf
                            self.logger.log(
                                user=f"User {self.user_id}",
                                action="Abmeldeknopf wurde gedrückt"
                            )
                        
                        # EXIT-TRIGGER (Pinch + Button)
                        elif self.exit_button.is_clicked(*cursor_pos):
                            should_exit = self.exit_button.click()
                            if should_exit:
                                # Logging für Programm-Beendigung
                                self.logger.log(
                                    user=f"User {self.user_id}",
                                    action="Programm beendet"
                                )
                                self.cap.release()
                                pygame.quit()
                                sys.exit()
                        
                        # Wenn außerhalb aller Menü-Buttons gepincht wird: Menü schließen
                        else:
                            self.menu_button.toggle()
                            self.logger.log(
                                user=f"User {self.user_id}",
                                action="Menü wurde geschlossen"
                            )
                    
                    # Menü ist NICHT offen: Normal funktionieren
                    else:
                        # Zurück-Button in Schlafzimmer-View
                        if self.ui and self.ui.current_view == "SCHLAFZIMMER":
                            if self.ui.schlafzimmer_view.back_button.is_clicked(*cursor_pos):
                                self.ui.current_view = "HOME"
                                self.logger.log(
                                    user=f"User {self.user_id}",
                                    action="Zurück zur HOME-View"
                                )
                        
                        # Menu Button
                        if self.menu_button.is_clicked(*cursor_pos):
                            self.menu_button.toggle()
                            # Logging für Menü
                            menu_state = "geöffnet" if self.menu_button.is_open else "geschlossen"
                            self.logger.log(
                                user=f"User {self.user_id}",
                                action=f"Menü wurde {menu_state}"
                            )
                        
                        # Räume (nur wenn Menü nicht offen)
                        else:
                            for room, rect in self.ui.room_zones.items():
                                if rect.collidepoint(self.cursor_x, self.cursor_y):
                                    if room == "Schlafzimmer":
                                        # Schlafzimmer: Wechsel zur Detail-View
                                        self.ui.current_view = "SCHLAFZIMMER"
                                        self.logger.log(
                                            user=f"User {self.user_id}",
                                            action=f"Zu {room} gewechselt"
                                        )
                                    else:
                                        # Andere Räume: Normale Toggle-Logik
                                        self.ui.select_room(room)
                                        self.ui.toggle_room(room)
                                        # Logging für Raum-Auswahl und Toggle
                                        room_state = "eingeschaltet" if self.ui.rooms[room] else "ausgeschaltet"
                                        self.logger.log(
                                            user=f"User {self.user_id}",
                                            action=f"{room} wurde {room_state}"
                                        )
                
                # Update pinch state for next frame
                self.last_pinch_active = pinch_active

                # Zustand speichern
                self.last_touching = touching

                # -------------------------------------------------
                # CURSOR ZEICHNEN
                # -------------------------------------------------
                if self.user_id == 1:
                    pygame.draw.circle(self.screen, color, (self.cursor_x, self.cursor_y), 10)

                elif self.user_id == 2:
                    rect = pygame.Rect(self.cursor_x - 10, self.cursor_y - 10, 20, 20)
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