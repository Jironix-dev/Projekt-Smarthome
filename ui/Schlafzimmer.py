# Kevin Wesner
# 26.01.26
# Schlafzimmer Nahaufnahme mit den Widgets

import pygame
from ui.zuruck_knopf import BackButton
from widgets.light import LightWidget 
from widgets.rollo import RolloWidget

class SchlafzimmerView:
    def __init__(self, ui):
        self.ui = ui
        self.screen = ui.screen
        self.font = ui.font

        # Schlafzimmer-Bild laden
        self.image = pygame.image.load("Bilder/Schlafzimmer.png").convert_alpha()

        self.image = pygame.transform.scale(self.image, (ui.WIDTH, ui.HEIGHT))

        # Menu Button wird von der UI bereitgestellt
        self.menu_button = ui.menu_button

        # Zurück-Button neben dem Menü-Button
        # Menu Button hat Größe 80x60 (width, height) bei Position (20, 20)
        # Zurück-Button soll rechts daneben sein
        back_button_x = self.menu_button.rect.x + self.menu_button.rect.width + 10  # 10px Abstand
        back_button_y = self.menu_button.rect.y
        self.back_button = BackButton(x=back_button_x, y=back_button_y, width=80, height=60)

        #Licht-Widget erzeugen
        self.light_widget = LightWidget(100, 200, name="Schlafzimmer Licht")

        #Rollo-Widget erzeugen
        self.rollo_widget = RolloWidget(100, 400, name="Schlafzimmer Rollo")


    def draw(self):
        # Hintergrund
        self.screen.blit(self.image, (0, 0))

        # Menu Button zeichnen
        self.menu_button.draw(self.screen)

        # Zurück-Button zeichnen
        self.back_button.draw(self.screen)

        #Licht Widget zeichnen
        self.light_widget.draw(self.screen)

        #Rollo Widget zeichnen
        self.rollo_widget.draw(self.screen)

    def handle_click(self, pos):
        if self.back_button.is_clicked(pos[0], pos[1]):
            self.ui.current_view = "HOME"