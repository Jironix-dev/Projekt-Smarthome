"""Erkennung einfacher Handgesten mit MediaPipe.

Dieses Modul stellt die Klasse `UserDetector` bereit, die aus einem RGB-Frame
einfache Gesten erkennt: Faust (gibt 1 zurück), offene Hand (gibt 2 zurück)
oder `None`, wenn keine bekannte Geste erkannt wurde. Die Implementierung ist
leichtgewichtig, damit sie in jedem Frame ausgeführt werden kann.
"""

import mediapipe as mp


class UserDetector:
    """Erkennt Login-Gesten in einem RGB-Bild.

    Unterstützte Gesten:
    - Faust -> Rückgabewert 1
    - Offene Hand -> Rückgabewert 2

    Die Methoden sind bewusst kurz und schnell gehalten, damit sie pro Frame
    aufgerufen werden können.
    """

    def __init__(self):
        # MediaPipe Hands mit maximal einer Hand initialisieren
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

    def detect_user(self, rgb_frame):
        """Verarbeitet `rgb_frame` und gibt die erkannte User-ID zurück.

        Args:
            rgb_frame: NumPy-Array im RGB-Format (MediaPipe erwartet RGB).

        Returns:
            int|None: 1 für Faust, 2 für offene Hand, oder None wenn nichts erkannt.
        """
        result = self.hands.process(rgb_frame)

        if not result.multi_hand_landmarks:
            return None

        lm = result.multi_hand_landmarks[0].landmark

        if self.is_fist(lm):
            return 1

        if self.is_open_hand(lm):
            return 2

        return None

    def is_fist(self, lm):
        """Gibt True zurück, wenn die Fingerkuppen unter ihren jeweiligen Basispunkten liegen.

        Diese einfache Heuristik vergleicht vertikal die Positionen von Fingerkuppen
        und den zugehörigen Basislandmarks für Zeigefinger, Mittelfinger, Ringfinger
        und kleinen Finger.
        """
        return all(
            lm[tip].y > lm[base].y for tip, base in [(8, 5), (12, 9), (16, 13), (20, 17)]
        )

    def is_open_hand(self, lm):
        """Gibt True zurück, wenn die Fingerkuppen über ihren Basispunkten liegen.

        Entspricht der negativen Bedingung von `is_fist` und identifiziert eine
        offene Hand.
        """
        return all(
            lm[tip].y < lm[base].y for tip, base in [(8, 5), (12, 9), (16, 13), (20, 17)]
        )