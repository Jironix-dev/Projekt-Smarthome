#Kevin Wesner
#26.01.26
#Schlafzimmer Nahaufnahme mit den Widgets

import pygame

class SchlafzimmerView:
    def __init__(self, ui):
        self.ui = ui
        self.screen = ui.screen
        self.font = ui.font

        # Schlafzimmer-Bild laden
        self.image = pygame.image.load(
            "Bilder/Schlafzimmer.png"
        ).convert_alpha()

        self.image = pygame.transform.scale(
            self.image,
            (ui.WIDTH, ui.HEIGHT)
        )

        # Zurück-Button
        self.back_button = pygame.Rect(20, ui.HEIGHT - 80, 200, 50)

    def draw(self):
        # Hintergrund
        self.screen.blit(self.image, (0, 0))

        # Zurück-Button
        pygame.draw.rect(self.screen, (50, 50, 50), self.back_button, border_radius=10)
        text = self.font.render("← Zurück", True, (255, 255, 255))
        self.screen.blit(
            text,
            (self.back_button.centerx - text.get_width() // 2,
             self.back_button.centery - text.get_height() // 2)
        )

    def handle_click(self, pos):
        if self.back_button.collidepoint(pos):
            self.ui.current_view = "HOME"