"""Anmelde-UI und Erkennungs-Wrapper.

Dieses Modul kapselt die Login-Zeichenlogik und die
stabillisierte Erkennungs-Logik (Debounce). Es zeigt kein
Kamerabild im Login-Bildschirm.
"""
import pygame
from vision.user_detection import UserDetector


class Anmeldung:
    def __init__(self, width: int, height: int, user_detector: UserDetector | None = None, threshold: int = 8):
        self.width = width
        self.height = height
        self.user_detector = user_detector or UserDetector()

        # Debounce / stable-frame state
        self.login_detect_candidate = None
        self.login_detect_counter = 0
        self.login_detect_threshold = threshold

    def process_frame(self, rgb_frame):
        """Analysiere ein RGB-Frame und gib die erkannte User-ID zurück
        sobald die Geste über mehrere Frames stabil erkannt wurde.

        Rückgabe: User-ID (z.B. 1/2) oder None
        """
        user = self.user_detector.detect_user(rgb_frame)
        if user is not None:
            if self.login_detect_candidate != user:
                self.login_detect_candidate = user
                self.login_detect_counter = 1
            else:
                self.login_detect_counter += 1

            if self.login_detect_counter >= self.login_detect_threshold:
                # Reset intern und bestätige Login
                confirmed = self.login_detect_candidate
                self.login_detect_candidate = None
                self.login_detect_counter = 0
                return confirmed
        else:
            self.login_detect_candidate = None
            self.login_detect_counter = 0

        return None

    def draw_login_screen(self, screen: pygame.Surface, title_font: pygame.font.Font, instr_font: pygame.font.Font, small_font: pygame.font.Font):
        """Zeichnet das Login-Panel (ohne Kamerabild)."""
        # background gradient (simple fill here, gradient handled by caller if desired)
        screen.fill((12, 16, 25))

        # centered panel using the actual surface size (keeps it centered if window changes)
        sw = screen.get_width()
        sh = screen.get_height()
        panel_w = int(sw * 0.7)
        panel_h = int(sh * 0.45)
        panel_x = (sw - panel_w) // 2
        panel_y = (sh - panel_h) // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (20, 20, 30, 230), (0, 0, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(panel, (100, 100, 120, 40), (0, 0, panel_w, panel_h), 2, border_radius=12)
        screen.blit(panel, (panel_x, panel_y))

        # Title
        title = title_font.render("Bitte Geste zeigen", True, (240, 240, 240))
        screen.blit(title, (panel_x + 20, panel_y + 20))

        # Instruction boxes
        box_w = (panel_w - 80) // 2
        box_h = 120
        left_x = panel_x + 20
        right_x = panel_x + 40 + box_w
        box_y = panel_y + 80

        # left box (Faust)
        lbox = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(lbox, (255, 255, 255, 12), (0, 0, box_w, box_h), border_radius=8)
        lbl1 = instr_font.render("Faust → Anmeldung: User 1", True, (230, 230, 230))
        lsub = small_font.render("Faust kurz zeigen", True, (180, 180, 180))
        lbox.blit(lbl1, (12, 12))
        lbox.blit(lsub, (12, 12 + lbl1.get_height() + 6))
        screen.blit(lbox, (left_x, box_y))

        # right box (open hand)
        rbox = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(rbox, (255, 255, 255, 12), (0, 0, box_w, box_h), border_radius=8)
        rlbl1 = instr_font.render("Offene Hand → Anmeldung: User 2", True, (230, 230, 230))
        rsub = small_font.render("Hand offen zeigen (Finger sichtbar)", True, (180, 180, 180))
        rbox.blit(rlbl1, (12, 12))
        rbox.blit(rsub, (12, 12 + rlbl1.get_height() + 6))
        screen.blit(rbox, (right_x, box_y))

        # hint
        hint = small_font.render("Warte auf Gestenerkennung...", True, (180, 180, 180))
        screen.blit(hint, (panel_x + 20, panel_y + panel_h - 30))

        # progress overlay
        if self.login_detect_candidate is not None:
            cand = self.login_detect_candidate
            ok_text = title_font.render(f"Erkannt: User {cand} ({self.login_detect_counter}/{self.login_detect_threshold})", True, (200, 255, 200))
            screen.blit(ok_text, ((sw - ok_text.get_width()) // 2, int(sh * 0.65)))
