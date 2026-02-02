#Kevin Wesner
#Widget für die Steuerung der Rollos 
#01.02.2026

import pygame


class RolloWidget:
    """
    Rollo-Widget mit vertikalem Slider rechts neben dem Widget.
    - Klick (Pinch-Start) auf das Widget: Rollo toggeln (offen/geschlossen)
    - Slider erscheint nur wenn Rollo offen ist
    - Slider vertikal: oben = 100%, unten = 0%
    - Zwischenstufen möglich
    """

    def __init__(self, x, y, width=220, height=120, name="Rollo"):
        self.rect = pygame.Rect(x, y, width, height)
        self.name = name

        # Rollo-Zustand
        self.is_open = True
        self.position = 100          # 100 = ganz oben (offen), 0 = ganz unten (geschlossen)
        self.last_position = 100

        # Slider rechts neben dem Widget
        self.slider_rect = pygame.Rect(
            self.rect.right + 10,
            self.rect.y,
            40,
            self.rect.height
        )

        self.slider_open = self.is_open  # Slider zeigen wenn Rollo offen ist
        self.is_hovered = False

        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 24)

    def draw(self, screen):
        # Hintergrund basierend auf Zustand
        if self.is_open:
            bg_color = (100, 180, 255)
        else:
            bg_color = (60, 60, 60)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=12)

        # Graue Füllung oben basierend auf Position (nur wenn offen)
        if self.is_open:
            fill_height = int(((100 - self.position) / 100) * self.rect.height)
            fill_rect = pygame.Rect(
                self.rect.x,
                self.rect.y,
                self.rect.width,
                fill_height
            )
            pygame.draw.rect(screen, (60, 60, 60), fill_rect, border_radius=12)

        # Lamellen-Look
        for i in range(5):
            lamelle_y = self.rect.y + 20 + i * 15
            pygame.draw.rect(
                screen,
                (120, 120, 120),
                (self.rect.x + 10, lamelle_y, self.rect.width - 20, 8),
                border_radius=4
            )

        # Randfarbe bei Hover
        border_color = (120, 170, 255) if self.is_hovered else (255, 255, 255)
        pygame.draw.rect(screen, border_color, self.rect, 3, border_radius=12)

        # Titel
        text = self.font.render(self.name, True, (0, 0, 0))
        screen.blit(text, (self.rect.x + 10, self.rect.y + 10))

        # Status
        status = f"{self.position}% offen" if self.is_open else "Geschlossen"
        status_text = self.font.render(status, True, (0, 0, 0))
        screen.blit(status_text, (self.rect.x + 10, self.rect.y + 50))

        # Vertikaler Slider
        if self.slider_open:
            pygame.draw.rect(screen, (100, 180, 255), self.slider_rect, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), self.slider_rect, 2, border_radius=10)

            # Füllhöhe berechnen (oben = 100%, unten = 0%)
            fill_height = int(((100 - self.position) / 100) * self.slider_rect.height)
            fill_y = self.slider_rect.y


            fill_rect = pygame.Rect(
                self.slider_rect.x,
                fill_y,
                self.slider_rect.width,
                fill_height
            )
            pygame.draw.rect(screen, (60, 60, 60), fill_rect, border_radius=10)

            # Griff (horizontaler Strich)
            handle_y = self.slider_rect.y + int((100 - self.position) / 100 * self.slider_rect.height)
            handle_height = 6
            handle_width = self.slider_rect.width - 10

            handle_rect = pygame.Rect(
                self.slider_rect.x + 5,
                handle_y - handle_height // 2,
                handle_width,
                handle_height
            )
            pygame.draw.rect(screen, (0, 0, 0), handle_rect, border_radius=3)

    def handle_gesture(self, cursor, pinch_start, pinch_active):
        if cursor is None or cursor[0] is None:
            self.is_hovered = False
            return

        cx, cy = cursor

        # Hover-Effekt
        self.is_hovered = self.rect.collidepoint((cx, cy))

        # Klick → Rollo toggeln
        if pinch_start and self.rect.collidepoint((cx, cy)):
            self.is_open = not self.is_open
            self.slider_open = self.is_open

            if self.is_open:
                self.position = self.last_position

            return

        # Vertikaler Slider
        if self.is_open and self.slider_open and pinch_active and self.slider_rect.collidepoint((cx, cy)):
            rel_y = cy - self.slider_rect.y
            rel_y = max(0, min(self.slider_rect.height, rel_y))

            self.position = 100 - int((rel_y / self.slider_rect.height) * 100)

            if self.position > 0:
                self.last_position = self.position

            # Wenn Slider zu 0% → Rollo schließen
            if self.position <= 2:
                self.position = 0
                self.is_open = False
                self.slider_open = False

            return

            return

