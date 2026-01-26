# Name: Kevin Dietrich
# Datum: 26.01.2026
# Projekt: Smart-Home

import pygame
import time


class ExitButton:
    def __init__(self, x, y, width=120, height=50):
        self.rect = pygame.Rect(x, y, width, height)

        # Normalzustand
        self.color_normal = (100, 100, 100)  # Grau
        self.text_normal = (255, 255, 255)  # Weiß
        self.text_content_normal = "Beenden"

        # Bestätigungszustand
        self.color_confirm = (255, 165, 0)  # Orange
        self.text_confirm = (0, 0, 0)  # Schwarz
        self.text_content_confirm = "Sicher?"

        # Aktuelle Werte
        self.current_color = self.color_normal
        self.current_text_color = self.text_normal
        self.current_text_content = self.text_content_normal

        # Bestätigungszustand
        self.is_confirming = False
        self.confirm_time = None
        self.confirm_timeout = 5.0  # 5 Sekunden

        self.radius = 10
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 24, bold=True)

    def draw(self, screen):
        """Zeichnet den Knopf auf den Screen."""
        pygame.draw.rect(
            screen,
            self.current_color,
            self.rect,
            border_radius=self.radius,
        )

        text_surface = self.font.render(self.current_text_content, True, self.current_text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, cursor_x, cursor_y):
        """Prüft, ob der Knopf angeklickt wurde."""
        return self.rect.collidepoint(cursor_x, cursor_y)

    def click(self):
        """Wird aufgerufen, wenn der Knopf geklickt wird."""
        if not self.is_confirming:
            # Wechsel zu Bestätigungsmodus
            self.is_confirming = True
            self.confirm_time = time.time()
            self.current_color = self.color_confirm
            self.current_text_color = self.text_confirm
            self.current_text_content = self.text_content_confirm
            return False  # Programm nicht beenden
        else:
            # Zweiter Klick → Programm beenden
            return True  # Programm beenden

    def update(self):
        """Aktualisiert den Zustand des Knopfs (z.B. Timeout-Check)."""
        if self.is_confirming and self.confirm_time is not None:
            elapsed_time = time.time() - self.confirm_time

            if elapsed_time > self.confirm_timeout:
                # Timeout → Zurücksetzen zu Normalzustand
                self.reset()

    def reset(self):
        """Setzt den Knopf auf den Normalzustand zurück."""
        self.is_confirming = False
        self.confirm_time = None
        self.current_color = self.color_normal
        self.current_text_color = self.text_normal
        self.current_text_content = self.text_content_normal
