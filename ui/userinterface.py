#Kevin Wesner
#Smart Home UI Startseite
#Erstellt am 26.01.26


import pygame
from ui.abmeldeknopf import LogoutButton
from ui.knopf_beenden import ExitButton
from ui.menu_knopf import MenuButton
from ui.Schlafzimmer import SchlafzimmerView

class SmartHomeUI:
    def __init__(self):
        pygame.init()

        # Fenster
        self.WIDTH = 1100
        self.HEIGHT = 650
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Gestenbasiertes Smart Home")

        self.clock = pygame.time.Clock()

        # Farben
        self.GREEN = (0, 200, 0)
        self.RED = (200, 0, 0)
        self.YELLOW = (255, 215, 0)
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)

        # Schrift
        self.font = pygame.font.SysFont("arial", 22, bold=True)

        # Grundriss PNG laden (proportional skalieren und zentrieren)
        img = pygame.image.load("Bilder/grundriss_neu.png").convert_alpha()
        img_width, img_height = img.get_size()
        window_ratio = self.WIDTH / self.HEIGHT
        img_ratio = img_width / img_height

        if img_ratio > window_ratio:
            # Bild ist breiter → Breite anpassen
            new_width = self.WIDTH
            new_height = int(self.WIDTH / img_ratio)
        else:
            # Bild ist höher → Höhe anpassen
            new_height = self.HEIGHT
            new_width = int(self.HEIGHT * img_ratio)

        self.floorplan = pygame.transform.scale(img, (new_width, new_height))
        self.floorplan_pos = ((self.WIDTH - new_width) // 2, (self.HEIGHT - new_height) // 2)

        # Smart-Home-Zustände
        self.rooms = {
            "Wohnzimmer": False,
            "Schlafzimmer": False
        }

        # Interaktionszonen (an Grundriss anpassen!)
        self.room_zones = {
            "Schlafzimmer": pygame.Rect(700, 100, 150, 100),
            "Wohnzimmer": pygame.Rect(250, 400, 150, 100)
        }

        # Aktuell ausgewählter Raum
        self.selected_room = None
        
        # Aktuelle Ansicht (HOME oder SCHLAFZIMMER)
        self.current_view = "HOME"
        
        # Menu Button
        self.menu_button = MenuButton(x=20, y=20)
        
        # Logout Button (nur im Menü sichtbar)
        self.logout_button = LogoutButton(x=20, y=90)
        
        # Exit Button (nur im Menü sichtbar)
        self.exit_button = ExitButton(x=20, y=160)
        
        # Schlafzimmer-View
        self.schlafzimmer_view = SchlafzimmerView(self)

    #Handtracking erkennen
    def toggle_room(self, room_name):
        #Schaltet Raum ein und aus
        if room_name in self.rooms:
            self.rooms[room_name] = not self.rooms[room_name]

    def select_room(self, room_name):
        #Markiert einen Raum als ausgewählt
        if room_name in self.rooms:
            self.selected_room = room_name

    # -------- Hintergrund-Farbverlauf --------
    def draw_gradient(self, surface, top_color, bottom_color):
        for y in range(self.HEIGHT):
            ratio = y / self.HEIGHT
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.WIDTH, y))

    # -------- Raum zeichnen --------
    def draw_room(self, name, rect, active, selected):
        # Schatten
        shadow_rect = rect.move(4, 4)
        pygame.draw.rect(self.screen, (0, 0, 0), shadow_rect, border_radius=10)

        # Hauptfläche
        color = self.GREEN if active else self.RED
        pygame.draw.rect(self.screen, color, rect, border_radius=10)

        # Rahmen
        if selected:
            pygame.draw.rect(self.screen, self.YELLOW, rect, 4, border_radius=10)
        else:
            pygame.draw.rect(self.screen, self.BLACK, rect, 2, border_radius=10)

        # Text
        text = self.font.render(name, True, self.WHITE)
        self.screen.blit(
            text,
            (rect.centerx - text.get_width() // 2,
             rect.centery - text.get_height() // 2)
        )

    # -------- Overlay für Fokus --------
    def draw_focus_overlay(self, selected_rect):
        # Abdunkeln der gesamten Fläche
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))

        # Ausgewählter Raum wieder hervorheben
        room = selected_rect
        color = self.GREEN if self.rooms[self.selected_room] else self.RED
        pygame.draw.rect(self.screen, color, room, border_radius=10)
        pygame.draw.rect(self.screen, self.YELLOW, room, 4, border_radius=10)

    # -------- Hauptloop --------
    def run(self):
        running = True
        while running:
            self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Mausklick, um ins Schlafzimmer zu wechseln
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.current_view == "HOME":
                        for room, rect in self.room_zones.items():
                            if rect.collidepoint(event.pos):
                                if room == "Schlafzimmer":
                                    self.current_view = "SCHLAFZIMMER"
                                else:
                                    self.selected_room = room

                    elif self.current_view == "SCHLAFZIMMER":
                        self.schlafzimmer_view.handle_click(event.pos)

                # Zustand wechseln (Platzhalter für Geste)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.selected_room:
                        self.rooms[self.selected_room] = not self.rooms[self.selected_room]

            # -------- ZEICHNEN --------
            if self.current_view == "HOME":
                # Home View zeichnen
                self.draw_gradient(self.screen, (20, 25, 40), (10, 10, 10))
                self.screen.blit(self.floorplan, self.floorplan_pos)

                # Overlay nur, wenn ein Raum ausgewählt ist
                if self.selected_room:
                    self.draw_focus_overlay(self.room_zones[self.selected_room])

                # Alle Räume zeichnen, nicht ausgewählte
                for room, rect in self.room_zones.items():
                    if room != self.selected_room:
                        self.draw_room(room, rect, self.rooms[room], False)

                # Logout Button
                self.logout_button.draw(self.screen)
            
            elif self.current_view == "SCHLAFZIMMER":
                # Schlafzimmer View zeichnen
                self.schlafzimmer_view.draw()

            pygame.display.flip()

        pygame.quit()