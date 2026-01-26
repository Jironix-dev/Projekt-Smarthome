#Name: Kevin Dietrich
#Datum: 26.01.2026
#Projekt: Smart-Home

import pygame


class MenuButton:
    def __init__(self, x, y, width=80, height=60):
        self.rect = pygame.Rect(x, y, width, height)
        self.initial_x = x
        self.initial_y = y

        # Normalzustand
        self.color_normal = (100, 100, 100)      # Grau
        self.text_normal = (255, 255, 255)       # Weiß

        # Geöffnet-Zustand
        self.color_open = (50, 50, 50)           # Dunkelgrau
        self.text_open = (200, 200, 200)         # Hellgrau

        # Aktuelle Farben
        self.current_color = self.color_normal
        self.current_text_color = self.text_normal

        self.radius = 10
        self.is_open = False
        
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 20, bold=True)

    def draw(self, screen):
        """Zeichnet den Menü-Knopf auf den Screen."""
        pygame.draw.rect(
            screen,
            self.current_color,
            self.rect,
            border_radius=self.radius
        )

        text_surface = self.font.render("Menü", True, self.current_text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, cursor_x, cursor_y):
        """Prüft, ob der Knopf angeklickt wurde."""
        return self.rect.collidepoint(cursor_x, cursor_y)

    def toggle(self):
        """Öffnet oder schließt das Menü."""
        self.is_open = not self.is_open
        if self.is_open:
            self.current_color = self.color_open
            self.current_text_color = self.text_open
        else:
            self.current_color = self.color_normal
            self.current_text_color = self.text_normal

    def draw_overlay(self, screen, width, height):
        """Zeichnet ein halbtransparentes Overlay über dem Bildschirm."""
        if self.is_open:
            overlay = pygame.Surface((width, height))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            screen.blit(overlay, (0, 0))
