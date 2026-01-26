"""LabelManager: kompakter Helfer zur Vorberechnung von Raum-Labels.

Dieses Modul zentralisiert das Rendern der Raum-Beschriftungen, sodass die
UI vorgerenderte Surfaces verwenden kann, anstatt in jedem Frame
`font.render` aufzurufen.
"""

import pygame


class LabelManager:
    """Bereitet Raum-Labels vor und blittet sie mit kleinem Hintergrund.

    Der Manager berechnet für jedes Raum-Polygon eine einfache Bounding-Box
    und legt zwei Label-Surfaces pro Raum an (normal und selektiert). Nutze
    `blit_label(screen, room, is_selected)`, um die passende Surface zu zeichnen.
    """

    def __init__(self, font, floorplan, floorplan_pos, room_zones):
        self.font = font
        self.floorplan = floorplan
        self.floorplan_pos = floorplan_pos
        self.room_zones = room_zones

        self.room_bboxes = {}
        self.label_surfaces = {}
        self._prepare()

    def _centroid(self, shape):
        """Gibt das Zentrum (Centroid) für ein Polygon oder ein Rect zurück."""
        if isinstance(shape, pygame.Rect):
            return shape.center
        cx = sum(p[0] for p in shape) // len(shape)
        cy = sum(p[1] for p in shape) // len(shape)
        return (cx, cy)

    def _label_pos(self, room, shape):
        """Berechnet eine sichere Label-Position: Centroid falls im Grundriss,
        sonst eine definierte Fallback-Position."""
        cx, cy = self._centroid(shape)
        fp_x, fp_y = self.floorplan_pos
        fp_w, fp_h = self.floorplan.get_width(), self.floorplan.get_height()
        if fp_x <= cx <= fp_x + fp_w and fp_y <= cy <= fp_y + fp_h:
            return (cx, cy)
        # reasonable fallbacks per room to avoid off-screen labels
        mapping = {
            "Badezimmer": (0.15, 0.15),
            "Schlafzimmer": (0.75, 0.15),
            "Wohnzimmer": (0.25, 0.75),
            "Kueche": (0.75, 0.75),
        }
        frac = mapping.get(room, (0.5, 0.5))
        return (int(fp_x + frac[0] * fp_w), int(fp_y + frac[1] * fp_h))

    def _prepare(self):
        """Bereitet Bounding-Boxen und gecachte Label-Surfaces für alle Räume vor."""
        pad_x, pad_y = 10, 6
        for room, shape in self.room_zones.items():
            # bounding box for a quick point-in-room rejection
            if isinstance(shape, pygame.Rect):
                xs = [shape.left, shape.right]
                ys = [shape.top, shape.bottom]
            else:
                xs = [p[0] for p in shape]
                ys = [p[1] for p in shape]
            self.room_bboxes[room] = (min(xs), min(ys), max(xs), max(ys))

            # render text once for normal and selected states
            txt_normal = self.font.render(room, True, (0, 0, 0))
            txt_sel = self.font.render(room, True, (255, 255, 255))

            w1 = txt_normal.get_width() + pad_x * 2
            h1 = txt_normal.get_height() + pad_y * 2
            surf_normal = pygame.Surface((w1, h1), pygame.SRCALPHA)
            pygame.draw.rect(surf_normal, (255, 255, 255, 200), (0, 0, w1, h1), border_radius=6)
            surf_normal.blit(txt_normal, (pad_x, pad_y))

            w2 = txt_sel.get_width() + pad_x * 2
            h2 = txt_sel.get_height() + pad_y * 2
            surf_sel = pygame.Surface((w2, h2), pygame.SRCALPHA)
            pygame.draw.rect(surf_sel, (0, 0, 0, 180), (0, 0, w2, h2), border_radius=6)
            surf_sel.blit(txt_sel, (pad_x, pad_y))

            pos = self._label_pos(room, shape)
            # store top-left positions for blitting
            self.label_surfaces[room] = {
                "normal": (surf_normal, (pos[0] - w1 // 2, pos[1] - h1 // 2)),
                "selected": (surf_sel, (pos[0] - w2 // 2, pos[1] - h2 // 2)),
            }

    def get_label_surface(self, room, is_selected):
        """Gibt ein Tupel (surface, topleft) für den gewünschten Label-Zustand zurück."""
        entry = self.label_surfaces.get(room)
        if not entry:
            return None, (0, 0)
        key = "selected" if is_selected else "normal"
        return entry[key]

    def blit_label(self, screen, room, is_selected):
        """Blitt die vorbereitete Label-Surface für `room` auf `screen`."""
        surf, topleft = self.get_label_surface(room, is_selected)
        if surf:
            screen.blit(surf, topleft)
