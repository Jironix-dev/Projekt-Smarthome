# Name: Kevin Dietrich
# Datum: 26.01.2026
# Projekt: Smart-Home
# Kamera-Feed Anzeige in der unteren rechten Ecke

import cv2
import pygame

# ============================================
# KONFIGURATION - KAMERA-ANZEIGE AKTIVIEREN/DEAKTIVIEREN
# ============================================
# Setze auf 1, um das Kamerabild anzuzeigen
# Setze auf 0, um das Kamerabild auszublenden
KAMERA_ANZEIGE_AKTIV = 0
# ============================================


class KameraAnzeige:
    def __init__(self, fenster_breite, fenster_hoehe):
        # Die übergebenen Fenstermaße werden hier nicht benötigt
        # Größe des Mini-Feeds (Aspect Ratio beibehalten)
        self.feed_width = 200
        self.feed_height = 150

    def draw_camera_feed(self, screen, rgb_frame):
        """
        Zeichnet den Kamera-Feed in der unteren rechten Ecke

        Args:
            screen: pygame screen Objekt
            rgb_frame: Das RGB-Frame Bild von MediaPipe
        """
        # Wenn Anzeige deaktiviert ist, nicht zeichnen
        if not KAMERA_ANZEIGE_AKTIV:
            return

        # Skaliere das RGB-Frame-Bild auf die gewünschte Feed-Größe
        if rgb_frame is None:
            return

        small_frame = cv2.resize(rgb_frame, (self.feed_width, self.feed_height))

        # Erzeuge pygame Surface (einfach, zuverlässig)
        try:
            buf = small_frame.astype('uint8').tobytes()
            small_surface = pygame.image.frombuffer(buf, (self.feed_width, self.feed_height), 'RGB')
            small_surface = small_surface.convert()
        except Exception:
            # Fallback auf surfarray (Transpose nötig)
            small_surface = pygame.surfarray.make_surface(small_frame.transpose((1, 0, 2)))
            small_surface = small_surface.convert()

        # Positioniere in der unteren rechten Ecke basierend auf der echten Screen-Größe
        margin_right = 10
        margin_bottom = 10
        screen_w, screen_h = screen.get_size()
        feed_w, feed_h = small_surface.get_size()

        pos_x = max(0, screen_w - feed_w - margin_right)
        pos_y = max(0, screen_h - feed_h - margin_bottom)

        # Rahmen um den Feed
        pygame.draw.rect(screen, (255, 255, 255), (pos_x - 2, pos_y - 2, feed_w + 4, feed_h + 4), 2)

        # Zeichne das Bild
        screen.blit(small_surface, (pos_x, pos_y))
