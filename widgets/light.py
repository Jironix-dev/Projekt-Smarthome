#Kevin Wesner
#27.01.26
#Modulares Licht Widget Lich An/Aus/Dimmen nutzbar für alle Räume
import pygame


class LightWidget:
    """
    Modernes Licht-Widget mit ausklappbarem Slider.
    - Klick (Pinch-Start) auf das Widget: Slider erscheint
    - Pinch-Active + Cursor bewegen: Helligkeit ändern
    """

    def __init__(self, x, y, width=220, height=120, name="Licht"):
        self.rect = pygame.Rect(x, y, width, height)
        self.name = name

        # Lichtzustände
        self.is_on = False
        self.brightness = 100

        # Slider-Zustände
        self.slider_open = False
        self.slider_rect = pygame.Rect(x, y + height + 10, width, 40)
        self.slider_handle_x = x + int((self.brightness / 100) * width)

        # Gesten
        self._dragging_slider = False

        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 24)
        self.brightness = 100
        self.last_brightness = 100
        
        #Mit Hand über Widget fahren
        self.is_hovered = False

    # ---------------------------------------------------------
    # Zeichnen
    # ---------------------------------------------------------
    def draw(self, screen):
        # Widget Hintergrund
        bg_color = (255, 230, 140) if self.is_on else (70, 70, 70)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=12)

       # Hover-Randfarbe
        border_color = (255, 220, 0) if self.is_hovered else (255, 255, 255)
        pygame.draw.rect(screen, border_color, self.rect, 3, border_radius=12)

        # Text
        text = self.font.render(self.name, True, (0, 0, 0))
        screen.blit(text, (self.rect.x + 10, self.rect.y + 10))

        status = f"{self.brightness}%" if self.is_on else "Aus"
        status_text = self.font.render(status, True, (0, 0, 0))
        screen.blit(status_text, (self.rect.x + 10, self.rect.y + 50))

        # ---------------------------------------------------------
        # Slider zeichnen, falls geöffnet
        # ---------------------------------------------------------
        if self.slider_open:
            pygame.draw.rect(screen, (50, 50, 50), self.slider_rect, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), self.slider_rect, 2, border_radius=10)

            # Slider-Füllung
            fill_rect = pygame.Rect(
                self.slider_rect.x,
                self.slider_rect.y,
                int((self.brightness / 100) * self.slider_rect.width),
                self.slider_rect.height
            )
            pygame.draw.rect(screen, (255, 200, 80), fill_rect, border_radius=10)

            # Slider-Griff
            handle_x = self.slider_rect.x + int((self.brightness / 100) * self.slider_rect.width)
            
            handle_width = 6
            handle_height = self.slider_rect.height - 10  # etwas kleiner als der Slider
            handle_rect = pygame.Rect(
                 handle_x - handle_width // 2,
                 self.slider_rect.y + 5,
                 handle_width,
                 handle_height
            )
            pygame.draw.rect(screen, (0, 0, 0), handle_rect, border_radius=3)


    # ---------------------------------------------------------
    # Gestensteuerung
    # ---------------------------------------------------------
    def handle_gesture(self, cursor, pinch_start, pinch_active):
        if cursor is None or cursor[0] is None:
            self._dragging_slider = False
            return
        cx, cy = cursor

    # Hover-Effekt
        if self.rect.collidepoint((cx, cy)):
            self.is_hovered = True
        else:
            self.is_hovered = False


    # 1) Klick auf das Widget → Licht toggeln + Slider steuern
        if pinch_start and self.rect.collidepoint(cx, cy):
        # Licht toggeln
            self.is_on = not self.is_on
            if self.is_on:
        # Licht geht an → alte Helligkeit wiederherstellen
                self.brightness = self.last_brightness
                self.slider_open = True
            else:
        # Licht geht aus → Helligkeit NICHT löschen
                self.slider_open = False

            return


    # 2) Slider bedienen (nur wenn Licht an ist)
        if self.is_on and self.slider_open and pinch_active and self.slider_rect.collidepoint(cx, cy):
            rel_x = cx - self.slider_rect.x
            rel_x = max(0, min(self.slider_rect.width, rel_x))
            self.brightness = int((rel_x / self.slider_rect.width) * 100)

        #letzte Helligkeit speichern
        if self.brightness > 0:
            self.last_brightness = self.brightness

        # Wenn Helligkeit 0 → Licht aus + Slider schließen
            if self.brightness == 0:
                self.is_on = False
                self.slider_open = False

            return

