"""Haupt-UI für das gestenbasierten Smart Home.

Die Klasse `SmartHomeUI` verwaltet das Pygame-Fenster, zeichnet den
Grundriss, verwaltet Raum-Zustände und stellt die Raum-Views bereit.
"""

import pygame
import os
import json
from ui.abmeldeknopf import LogoutButton
from ui.knopf_beenden import ExitButton
from ui.menu_knopf import MenuButton
from ui.Schlafzimmer import SchlafzimmerView
from ui.Wohnzimmer import WohnzimmerView
from ui.badezimmer import BadezimmerView
from ui.kueche import KuecheView
from ui.label_manager import LabelManager


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

        # Interaktionszonen werden via Polygone definiert (keine externen Masken)

        # Smart-Home-Zustände
        self.rooms = {
            "Wohnzimmer": False,
            "Schlafzimmer": False,
            "Badezimmer": False,
            "Kueche": False,
        }

        # Interaktionszonen (an Grundriss anpassen!)
        # Versuche zuerst, polygonale Definitionen aus `room_polygons.json` zu laden.
        # Die Datei sollte normalisierte Koordinaten (0..1) relativ zum Floorplan-Bild enthalten.
        jp = os.path.join(os.getcwd(), "tools", "room_polygons.json")
        loaded = None
        if os.path.exists(jp):
            try:
                with open(jp, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
            except Exception:
                loaded = None

        if loaded:
            # convert normalized coordinates into screen coordinates (floorplan_pos + scaled)
            fp_w, fp_h = self.floorplan.get_width(), self.floorplan.get_height()
            self.room_zones = {}
            for room, pts in loaded.items():
                try:
                    conv = [
                        (int(self.floorplan_pos[0] + x * fp_w), int(self.floorplan_pos[1] + y * fp_h))
                        for (x, y) in pts
                    ]
                    self.room_zones[room] = conv
                except Exception:
                    pass
        else:
            # Default polygon approximations (falls keine JSON vorhanden)
            self.room_zones = {
                "Badezimmer": [(150, 80), (420, 80), (420, 260), (150, 260)],
                "Schlafzimmer": [(600, 60), (980, 60), (980, 300), (600, 300)],
                "Wohnzimmer": [(120, 300), (520, 300), (520, 560), (120, 560)],
                "Kueche": [(560, 320), (1020, 320), (1020, 560), (560, 560)],
            }

        # compact label manager: precomputes bboxes and cached label surfaces
        self.label_manager = LabelManager(self.font, self.floorplan, self.floorplan_pos, self.room_zones)

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

        # Raum-Views
        self.schlafzimmer_view = SchlafzimmerView(self)
        self.wohnzimmer_view = WohnzimmerView(self)
        self.badezimmer_view = BadezimmerView(self)
        self.kueche_view = KuecheView(self)

    # Handtracking erkennen
    def toggle_room(self, room_name):
        # Schaltet Raum ein und aus
        if room_name in self.rooms:
            self.rooms[room_name] = not self.rooms[room_name]

    def select_room(self, room_name):
        # Markiert einen Raum als ausgewählt
        if room_name in self.rooms:
            self.selected_room = room_name

    def point_in_polygon(self, x, y, polygon):
        # Ray-casting algorithm for point-in-polygon
        inside = False
        n = len(polygon)
        for i in range(n):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % n]
            # Check if point is between y1 and y2
            if (y1 > y) != (y2 > y):
                # compute x coordinate of intersection
                xinters = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if xinters > x:
                    inside = not inside
        return inside

    def is_point_in_room(self, x, y, room_name):
        shape = self.room_zones.get(room_name)
        if shape is None:
            return False
        # quick bbox check via label_manager
        bbox = self.label_manager.room_bboxes.get(room_name)
        if bbox and (x < bbox[0] or x > bbox[2] or y < bbox[1] or y > bbox[3]):
            return False
        # Backwards-compatibility: if Rect object was used
        if isinstance(shape, pygame.Rect):
            return shape.collidepoint(x, y)
        # otherwise assume polygon list
        return self.point_in_polygon(x, y, shape)

    def get_room_centroid(self, shape):
        # return centroid (x,y) for polygon or rect
        if isinstance(shape, pygame.Rect):
            return shape.center
        cx = sum([p[0] for p in shape]) // len(shape)
        cy = sum([p[1] for p in shape]) // len(shape)
        return (cx, cy)

    def draw_text_with_outline(self, text, pos, color, outline_color=(255, 255, 255)):
        # Render outline by drawing the text shifted in 8 directions, then the main text on top
        txt_surf = self.font.render(text, True, color)
        outline_surf = self.font.render(text, True, outline_color)
        x, y = pos
        # draw outline offsets
        offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for ox, oy in offsets:
            self.screen.blit(
                outline_surf, (x + ox - outline_surf.get_width() // 2, y + oy - outline_surf.get_height() // 2)
            )
        # draw main
        self.screen.blit(txt_surf, (x - txt_surf.get_width() // 2, y - txt_surf.get_height() // 2))

    def draw_label_with_background(self, text, pos, is_selected):
        # Draw a small rounded background behind the label for guaranteed readability
        txt_surf = self.font.render(text, True, self.WHITE if is_selected else self.BLACK)
        padding_x = 10
        padding_y = 6
        w = txt_surf.get_width() + padding_x * 2
        h = txt_surf.get_height() + padding_y * 2
        # background color: dark translucent when selected (white text), light translucent otherwise
        if is_selected:
            bg_color = (0, 0, 0, 180)
        else:
            bg_color = (255, 255, 255, 200)

        bg_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, bg_color, (0, 0, w, h), border_radius=6)

        x, y = pos
        dest_x = x - w // 2
        dest_y = y - h // 2
        self.screen.blit(bg_surf, (dest_x, dest_y))
        # blit text centered inside bg
        text_x = dest_x + padding_x
        text_y = dest_y + padding_y
        self.screen.blit(txt_surf, (text_x, text_y))

    def get_label_position(self, room, shape):
        # compute centroid, but ensure it's inside the floorplan; otherwise fallback to quadrant positions
        cx, cy = self.get_room_centroid(shape)
        fp_x, fp_y = self.floorplan_pos
        fp_w, fp_h = self.floorplan.get_width(), self.floorplan.get_height()
        # check if centroid is inside floorplan bounding box
        if fp_x <= cx <= fp_x + fp_w and fp_y <= cy <= fp_y + fp_h:
            return (cx, cy)

        # fallback positions per room (relative to floorplan)
        mapping = {
            "Badezimmer": (0.15, 0.15),
            "Schlafzimmer": (0.75, 0.15),
            "Wohnzimmer": (0.25, 0.75),
            "Kueche": (0.75, 0.75),
        }
        frac = mapping.get(room, (0.5, 0.5))
        return (int(fp_x + frac[0] * fp_w), int(fp_y + frac[1] * fp_h))

    # -------- Hintergrund-Farbverlauf (optimiert) --------
    def draw_gradient(self, surface, top_color, bottom_color):
        # Erstelle Gradient einmalig als Oberfläche
        if not hasattr(self, "_gradient_cache") or self._gradient_cache is None:
            gradient_surf = pygame.Surface((self.WIDTH, self.HEIGHT))
            for y in range(self.HEIGHT):
                ratio = y / self.HEIGHT
                r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
                g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
                b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
                pygame.draw.line(gradient_surf, (r, g, b), (0, y), (self.WIDTH, y))
            self._gradient_cache = gradient_surf

        surface.blit(self._gradient_cache, (0, 0))

    # -------- Raum zeichnen --------
    def draw_room(self, name, shape, active, selected):
        # Zeichnet nur die Hervorhebung (Füllung + gelbe Umrandung) wenn selected=True.
        if not selected:
            return

        # halbtransparente Füllung (leichtes Aufhellen)
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        fill_color = (255, 215, 0, 40)  # gelb mit geringer Alpha

        if isinstance(shape, pygame.Rect):
            pygame.draw.rect(overlay, fill_color, shape, border_radius=10)
            self.screen.blit(overlay, (0, 0))
            pygame.draw.rect(self.screen, self.YELLOW, shape, 5, border_radius=10)
        else:
            pygame.draw.polygon(overlay, fill_color, shape)
            self.screen.blit(overlay, (0, 0))
            pygame.draw.polygon(self.screen, self.YELLOW, shape, 5)

    def prepare_label_surfaces(self):
        # create combined bg+text surfaces for each room for normal and selected states
        self.label_surfaces = {}
        padding_x = 10
        padding_y = 6
        for room in self.room_zones.keys():
            # compute text surfaces
            txt_normal = self.font.render(room, True, self.BLACK)
            txt_selected = self.font.render(room, True, self.WHITE)

            w1 = txt_normal.get_width() + padding_x * 2
            h1 = txt_normal.get_height() + padding_y * 2
            surf_normal = pygame.Surface((w1, h1), pygame.SRCALPHA)
            pygame.draw.rect(surf_normal, (255, 255, 255, 200), (0, 0, w1, h1), border_radius=6)
            surf_normal.blit(txt_normal, (padding_x, padding_y))

            w2 = txt_selected.get_width() + padding_x * 2
            h2 = txt_selected.get_height() + padding_y * 2
            surf_selected = pygame.Surface((w2, h2), pygame.SRCALPHA)
            pygame.draw.rect(surf_selected, (0, 0, 0, 180), (0, 0, w2, h2), border_radius=6)
            surf_selected.blit(txt_selected, (padding_x, padding_y))

            # position (center) determined by get_label_position
            pos = self.get_label_position(room, self.room_zones[room])
            self.label_surfaces[room] = {
                "normal": (surf_normal, (pos[0] - w1 // 2, pos[1] - h1 // 2)),
                "selected": (surf_selected, (pos[0] - w2 // 2, pos[1] - h2 // 2)),
                "pos_center": pos,
            }

    def get_label_surface(self, room, is_selected):
        return self.label_manager.get_label_surface(room, is_selected)

    # -------- Overlay für Fokus --------
    def draw_focus_overlay(self, selected_shape):
        # Abdunkeln der gesamten Fläche
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))

        # Ausgewählter Raum wieder hervorheben (Polygon oder Rect)
        color = self.GREEN if self.rooms[self.selected_room] else self.RED
        if isinstance(selected_shape, pygame.Rect):
            pygame.draw.rect(self.screen, color, selected_shape, border_radius=10)
            pygame.draw.rect(self.screen, self.YELLOW, selected_shape, 4, border_radius=10)
        else:
            pygame.draw.polygon(self.screen, color, selected_shape)
            pygame.draw.polygon(self.screen, self.YELLOW, selected_shape, 4)

    # -------- Hauptloop --------
    def run(self):
        running = True
        while running:
            self.clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Mausklick, um in Raum-Details zu wechseln
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.current_view == "HOME":
                        for room, shape in self.room_zones.items():
                            if self.is_point_in_room(event.pos[0], event.pos[1], room):
                                if room == "Schlafzimmer":
                                    self.current_view = "SCHLAFZIMMER"
                                elif room == "Wohnzimmer":
                                    self.current_view = "WOHNZIMMER"
                                elif room == "Badezimmer":
                                    self.current_view = "BADEZIMMER"
                                elif room == "Kueche":
                                    self.current_view = "KUECHE"
                                else:
                                    self.selected_room = room

                    elif self.current_view == "SCHLAFZIMMER":
                        self.schlafzimmer_view.handle_click(event.pos)
                    elif self.current_view == "WOHNZIMMER":
                        self.wohnzimmer_view.handle_click(event.pos)
                    elif self.current_view == "BADEZIMMER":
                        self.badezimmer_view.handle_click(event.pos)
                    elif self.current_view == "KUECHE":
                        self.kueche_view.handle_click(event.pos)

                # Zustand wechseln (Platzhalter für Geste)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.selected_room:
                        self.rooms[self.selected_room] = not self.rooms[self.selected_room]

            # -------- ZEICHNEN --------
            if self.current_view == "HOME":
                # Home View zeichnen (Grundriss)
                self.draw_gradient(self.screen, (20, 25, 40), (10, 10, 10))
                self.screen.blit(self.floorplan, self.floorplan_pos)

                # floorplan bounding box (hidden in normal mode)
                fp_w, fp_h = self.floorplan.get_width(), self.floorplan.get_height()

                # Hover-Detection (Maus)
                mouse_x, mouse_y = pygame.mouse.get_pos()
                hovered = None
                for room, shape in self.room_zones.items():
                    if self.is_point_in_room(mouse_x, mouse_y, room):
                        hovered = room
                        break

                # Interaktionszonen sind unsichtbar — nur Hover/Selection hervorheben
                for room, shape in self.room_zones.items():
                    is_selected = (room == self.selected_room) or (room == hovered)
                    if is_selected:
                        # Hervorhebung zeichnen
                        self.draw_room(room, shape, self.rooms[room], True)

                # Draw room labels: black by default, white when hovered/selected
                for room, shape in self.room_zones.items():
                    is_selected = (room == self.selected_room) or (room == hovered)
                    self.label_manager.blit_label(self.screen, room, is_selected)

            elif self.current_view == "SCHLAFZIMMER":
                # Schlafzimmer View zeichnen
                self.schlafzimmer_view.draw()

            elif self.current_view == "WOHNZIMMER":
                # Wohnzimmer View zeichnen
                self.wohnzimmer_view.draw()

            elif self.current_view == "BADEZIMMER":
                # Badezimmer View zeichnen
                self.badezimmer_view.draw()

            elif self.current_view == "KUECHE":
                # Küche View zeichnen
                self.kueche_view.draw()

            pygame.display.flip()

        pygame.quit()