"""Fenster- und Anzeige-Manager.

Dieses Modul übernimmt die komplette Pygame-Fenstersteuerung, die
Integration mit der `ui.SmartHomeUI` und nutzt `HandTracker` für
Hand-Erkennung. Alle UI-/View-Wechsel- und Button-Interaktionen
leben hier.
"""

import cv2
import pygame
import sys

from vision.handtracking import HandTracker
from vision.user_detection import UserDetector
from vision.kamera_anzeige import KameraAnzeige
from vision.Anmeldung import Anmeldung
from logsystem.logger import Logger
from ui.userinterface import SmartHomeUI


class AnzeigeFenster:
    def __init__(self, width=1280, height=720, ui: SmartHomeUI | None = None):
        pygame.init()
        self.width = width
        self.height = height

        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Handtracking – Anzeige")
        self.clock = pygame.time.Clock()

        # UI: entweder externe SmartHomeUI verwenden oder selbst erstellen
        self.ui = ui or SmartHomeUI()
        # ensure UI draws into the same screen
        self.ui.screen = self.screen

        # Kamera-Anzeige (kleines Overlay)
        self.kamera_anzeige = KameraAnzeige(width, height)

        # Hand-Tracker (nur Erkennung)
        self.tracker = HandTracker(width, height)

        # User-Detection (für Login-Phase)
        self.user_detector = UserDetector()

        # Logging
        self.logger = Logger()

        # Login / state
        self.login_done = False
        self.user_id = None
        self.login_allowed = True
        self.login_cooldown = 0
        # delay (in seconds) before showing the login screen after logout
        self.login_delay_seconds = 0.5
        self.pending_logout = False
        # If set, freeze the cursor appearance (id + position) until cleared
        self.frozen_cursor_id = None
        self.frozen_cursor_pos = None
        # Anmeldung helper (separate module handles debounce and drawing)
        self.anmeldung = Anmeldung(width, height, self.user_detector, threshold=8)

        # Kamera
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(3, width)
        self.cap.set(4, height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        # Fonts für Login
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.instr_font = pygame.font.SysFont("Arial", 22)
        self.small_font = pygame.font.SysFont("Arial", 16)
        # Fonts für Login
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.instr_font = pygame.font.SysFont("Arial", 22)
        self.small_font = pygame.font.SysFont("Arial", 16)

    def run(self):
        while True:
            self.clock.tick(60)

            # Kamera frame lesen
            success, frame = self.cap.read()
            if not success:
                continue

            if self.login_cooldown > 0:
                self.login_cooldown -= 1
                if self.login_cooldown == 0:
                    # cooldown finished -> allow login UI to appear
                    self.login_allowed = True

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # MediaPipe / Hand-Tracking
            res = self.tracker.process_frame(rgb_frame)
            result = res.get("result")
            cursor = res.get("cursor")
            pinch_active = res.get("pinch_active")
            pinch_start = res.get("pinch_start")
            touching = res.get("touching")
            
            #Widget Steuerung, wenn man den den Raum öffnet
            if self.ui.current_view == "SCHLAFZIMMER":
                self.ui.schlafzimmer_view.rollo_widget.handle_gesture(cursor, pinch_start, pinch_active)
                self.ui.schlafzimmer_view.light_widget.handle_gesture(
                    cursor,
                    pinch_start,
                    pinch_active
                )

            if self.ui.current_view == "WOHNZIMMER":
                self.ui.wohnzimmer_view.rollo_widget.handle_gesture(cursor, pinch_start, pinch_active)
                self.ui.wohnzimmer_view.light_widget.handle_gesture(
                    cursor,
                    pinch_start,
                    pinch_active
                )

            if self.ui.current_view == "KUECHE":
                self.ui.kueche_view.rollo_widget.handle_gesture(cursor, pinch_start, pinch_active)
                self.ui.kueche_view.light_widget.handle_gesture(
                    cursor,
                    pinch_start,
                    pinch_active
                )

            if self.ui.current_view == "BADEZIMMER":
                self.ui.badezimmer_view.rollo_widget.handle_gesture(cursor, pinch_start, pinch_active)
                self.ui.badezimmer_view.light_widget.handle_gesture(
                    cursor,
                    pinch_start,
                    pinch_active
                )
            
            

            hands_in_frame = bool(result.multi_hand_landmarks) if result is not None else False
            # Pending logout: Abmelden wenn Hand verschwunden
            if self.pending_logout and not hands_in_frame:
                # perform actual logout now that the hand left the frame
                self.logger.log(user=f"User {self.user_id}", action="Abmeldung durchgeführt")
                self.login_done = False
                self.user_id = None
                self.pending_logout = False
                try:
                    self.ui.logout_button.reset()
                except Exception:
                    pass
                if self.ui.menu_button.is_open:
                    self.ui.menu_button.toggle()
                # clear frozen cursor appearance now that logout completed
                self.frozen_cursor_id = None
                self.frozen_cursor_pos = None
                # start delay before showing the login screen
                self.login_allowed = False
                self.login_cooldown = int(self.login_delay_seconds * 60)

            # Login-Phase: erkennungsbasiert (delegiert an Anmeldung)
            if not self.login_done and self.login_allowed and self.login_cooldown == 0:
                # draw login UI (no camera preview)
                self.anmeldung.draw_login_screen(self.screen, self.title_font, self.instr_font, self.small_font)

                user = self.anmeldung.process_frame(rgb_frame)
                if user is not None:
                    # clear any frozen cursor when a new user logs in
                    self.frozen_cursor_id = None
                    self.frozen_cursor_pos = None
                    self.user_id = user
                    self.login_done = True
                    self.login_allowed = False
                    try:
                        self.ui.logout_button.reset()
                    except Exception:
                        pass
                    self.logger.log(user=f"User {user}", action="Anmeldung erfolgreich")

                pygame.display.flip()
                continue

            # Normales Tracking / Zeichnen
            self.screen.fill((0, 0, 0))

            # Zeichne UI je nach View
            if self.ui.current_view == "HOME":
                self.ui.draw_gradient(self.screen, (20, 25, 40), (10, 10, 10))
                self.screen.blit(self.ui.floorplan, self.ui.floorplan_pos)

                # Highlight selected/hovered Räume
                hovered = None
                if cursor and cursor[0] is not None:
                    cx, cy = cursor
                    for room, shape in self.ui.room_zones.items():
                        if self.ui.is_point_in_room(cx, cy, room):
                            hovered = room
                            break

                if self.ui.selected_room and not self.ui.menu_button.is_open:
                    try:
                        self.ui.draw_focus_overlay(self.ui.room_zones[self.ui.selected_room])
                    except Exception:
                        pass

                if not self.ui.menu_button.is_open:
                    for room, shape in self.ui.room_zones.items():
                        is_selected = (room == self.ui.selected_room) or (room == hovered)
                        if is_selected:
                            self.ui.draw_room(room, shape, self.ui.rooms[room], True)
                    for room, shape in self.ui.room_zones.items():
                        is_selected = (room == self.ui.selected_room) or (room == hovered)
                        try:
                            self.ui.label_manager.blit_label(self.screen, room, is_selected)
                        except Exception:
                            pass

            elif self.ui.current_view == "SCHLAFZIMMER":
                self.ui.schlafzimmer_view.draw()
            elif self.ui.current_view == "WOHNZIMMER":
                self.ui.wohnzimmer_view.draw()
            elif self.ui.current_view == "BADEZIMMER":
                self.ui.badezimmer_view.draw()
            elif self.ui.current_view == "KUECHE":
                self.ui.kueche_view.draw()

            # Menu Overlay
            if self.ui.menu_button.is_open:
                try:
                    self.ui.menu_button.draw_overlay(self.screen, self.width, self.height)
                except Exception:
                    pass

            if self.ui.current_view == "HOME":
                try:
                    self.ui.menu_button.draw(self.screen)
                except Exception:
                    pass

            # Menü Buttons zeichnen
            if self.ui.menu_button.is_open:
                try:
                    self.ui.logout_button.draw(self.screen)
                    if hasattr(self.ui.logout_button, "update"):
                        self.ui.logout_button.update()
                except Exception:
                    pass
                try:
                    self.ui.exit_button.draw(self.screen)
                    self.ui.exit_button.update()
                except Exception:
                    pass

            # Cursor zeichnen (nur visuell)
            # Prefer live cursor position if available; fall back to frozen position (should be None normally)
            draw_id = self.frozen_cursor_id if self.frozen_cursor_id is not None else (self.user_id or 0)
            draw_cursor_pos = cursor if cursor and cursor[0] is not None else self.frozen_cursor_pos
            self.tracker.draw_cursor(self.screen, draw_cursor_pos, draw_id)

            # Kamera-Feed
            try:
                self.kamera_anzeige.draw_camera_feed(self.screen, rgb_frame)
            except Exception:
                pass

            # Ausgelöste Pinch-Events verarbeiten (nur beim Start eines Pinches)
            if pinch_start:
                # Wenn ein Pending-Logout aktiv ist, ignorieren wir alle Interaktionen
                if self.pending_logout:
                    # Menü bleibt sichtbar und gedrückter Zustand bleibt erhalten; keine Klicks erlauben
                    pass
                else:
                    # Menü offen: nur Menü-Buttons verarbeiten
                    if self.ui.menu_button.is_open:
                        # Menu Button Toggle
                        if self.ui.menu_button.is_clicked(*cursor):
                            self.ui.menu_button.toggle()
                            menu_state = "geöffnet" if self.ui.menu_button.is_open else "geschlossen"
                            self.logger.log(user=f"User {self.user_id}", action=f"Menü wurde {menu_state}")

                        elif self.ui.logout_button.is_clicked(*cursor):
                            # Start pending logout: mark button pressed and wait for hand removal
                            self.logger.log(user=f"User {self.user_id}", action="Abmeldeknopf wurde gedrückt (pending)")
                            self.pending_logout = True
                            # visually mark button pressed
                            try:
                                self.ui.logout_button.set_pressed()
                            except Exception:
                                pass
                            # freeze cursor appearance (ID/shape) but allow position to continue following
                            try:
                                self.frozen_cursor_id = self.user_id
                                # do not freeze position; keep following the live cursor
                                self.frozen_cursor_pos = None
                            except Exception:
                                self.frozen_cursor_id = None
                                self.frozen_cursor_pos = None

                        elif self.ui.exit_button.is_clicked(*cursor):
                            should_exit = self.ui.exit_button.click()
                            if should_exit:
                                self.logger.log(user=f"User {self.user_id}", action="Programm beendet")
                                self.cap.release()
                                pygame.quit()
                                sys.exit()

                        else:
                            # außerhalb: Menü schließen
                            self.ui.menu_button.toggle()
                            self.logger.log(user=f"User {self.user_id}", action="Menü wurde geschlossen")

                    else:
                        # Menü geschlossen: Navigation
                        # Zurück-Buttons in Room-Views
                        if self.ui.current_view == "SCHLAFZIMMER":
                            if self.ui.schlafzimmer_view.back_button.is_clicked(*cursor):
                                self.ui.current_view = "HOME"
                                self.logger.log(user=f"User {self.user_id}", action="Zurück zur HOME-View")
                        if self.ui.current_view == "WOHNZIMMER":
                            if self.ui.wohnzimmer_view.back_button.is_clicked(*cursor):
                                self.ui.current_view = "HOME"
                                self.logger.log(user=f"User {self.user_id}", action="Zurück zur HOME-View")
                        if self.ui.current_view == "BADEZIMMER":
                            if self.ui.badezimmer_view.back_button.is_clicked(*cursor):
                                self.ui.current_view = "HOME"
                                self.logger.log(user=f"User {self.user_id}", action="Zurück zur HOME-View")
                        if self.ui.current_view == "KUECHE":
                            if self.ui.kueche_view.back_button.is_clicked(*cursor):
                                self.ui.current_view = "HOME"
                                self.logger.log(user=f"User {self.user_id}", action="Zurück zur HOME-View")

                        # Menu Button
                        if self.ui.menu_button.is_clicked(*cursor):
                            self.ui.menu_button.toggle()
                            menu_state = "geöffnet" if self.ui.menu_button.is_open else "geschlossen"
                            self.logger.log(user=f"User {self.user_id}", action=f"Menü wurde {menu_state}")

                        else:
                            # Räume (nur wenn Menü nicht offen) — aber nur aus HOME heraus auswählbar
                            if self.ui.current_view == "HOME" and cursor and cursor[0] is not None:
                                cx, cy = cursor
                                for room, shape in self.ui.room_zones.items():
                                    if self.ui.is_point_in_room(cx, cy, room):
                                        if room == "Schlafzimmer":
                                            self.ui.current_view = "SCHLAFZIMMER"
                                            self.logger.log(user=f"User {self.user_id}", action=f"Zu {room} gewechselt")
                                        elif room == "Wohnzimmer":
                                            self.ui.current_view = "WOHNZIMMER"
                                            self.logger.log(user=f"User {self.user_id}", action=f"Zu {room} gewechselt")
                                        elif room == "Badezimmer":
                                            self.ui.current_view = "BADEZIMMER"
                                            self.logger.log(user=f"User {self.user_id}", action=f"Zu {room} gewechselt")
                                        elif room == "Kueche":
                                            self.ui.current_view = "KUECHE"
                                            self.logger.log(user=f"User {self.user_id}", action=f"Zu {room} gewechselt")
                                        else:
                                            self.ui.select_room(room)
                                            self.ui.toggle_room(room)
                                            room_state = "eingeschaltet" if self.ui.rooms[room] else "ausgeschaltet"
                                            self.logger.log(user=f"User {self.user_id}", action=f"{room} wurde {room_state}")

            # Events (nur QUIT behandeln hier; UI weitere Events intern)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.cap.release()
                    pygame.quit()
                    sys.exit()

            pygame.display.flip()

        # cleanup
        self.cap.release()
        pygame.quit()

    def draw_gradient(self, surface, top_color, bottom_color):
        # simple vertical gradient
        h = self.height
        surf = pygame.Surface((self.width, h))
        for y in range(h):
            ratio = y / max(1, h - 1)
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.width, y))
        surface.blit(surf, (0, 0))
 
