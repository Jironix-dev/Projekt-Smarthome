#Name: Kevin Dietrich
#Datum: 26.01.2026
#Projekt: Smart-Home
#Kamera-Feed Anzeige in der unteren rechten Ecke

import cv2
import pygame

# ============================================
# KONFIGURATION - KAMERA-ANZEIGE AKTIVIEREN/DEAKTIVIEREN
# ============================================
# Setze auf 1, um das Kamerabild anzuzeigen
# Setze auf 0, um das Kamerabild auszublenden
KAMERA_ANZEIGE_AKTIV = 1
# ============================================


class KameraAnzeige:
    def __init__(self, fenster_breite, fenster_hoehe):
        self.fenster_breite = fenster_breite
        self.fenster_hoehe = fenster_hoehe
        
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
        
        # Skaliere das RGB-Frame-Bild
        small_frame = cv2.resize(rgb_frame, (self.feed_width, self.feed_height))
        
        # Konvertiere NumPy Array zu pygame Surface
        # RGB ist das richtige Format für pygame surfarray
        small_surface = pygame.surfarray.make_surface(small_frame.transpose((1, 0, 2)))
        
        # Position in der unteren rechten Ecke
        pos_x = self.fenster_breite - self.feed_width - 10
        pos_y = self.fenster_hoehe - self.feed_height - 10
        
        # Zeichne einen Rahmen um den Feed
        pygame.draw.rect(screen, (255, 255, 255), 
                        (pos_x - 2, pos_y - 2, self.feed_width + 4, self.feed_height + 4), 2)
        
        # Zeichne das Bild
        screen.blit(small_surface, (pos_x, pos_y))
