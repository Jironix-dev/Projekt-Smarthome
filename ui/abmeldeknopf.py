import pygame


class LogoutButton:
    def __init__(self, x, y, width=200, height=60):
        self.rect = pygame.Rect(x, y, width, height)

        # Normalzustand
        self.color_normal = (200, 0, 0)      # Rot
        self.text_normal = (255, 255, 255)   # Weiß

        # Gedrückt-Zustand
        self.color_pressed = (120, 0, 0)     # Dunkleres Rot
        self.text_pressed = (0, 0, 0)        # Schwarz

        # Aktuelle Farben
        self.current_color = self.color_normal
        self.current_text_color = self.text_normal

        self.radius = 15
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 32, bold=True)

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            self.current_color,
            self.rect,
            border_radius=self.radius
        )

        text_surface = self.font.render("Abmelden", True, self.current_text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, cursor_x, cursor_y):
        return self.rect.collidepoint(cursor_x, cursor_y)

    def set_pressed(self):
        """Button optisch auf 'gedrückt' setzen."""
        self.current_color = self.color_pressed
        self.current_text_color = self.text_pressed

    def reset(self):
        """Button wieder in Normalzustand setzen."""
        self.current_color = self.color_normal
        self.current_text_color = self.text_normal