import mediapipe as mp

class UserDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

    def detect_user(self, rgb_frame):
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
        return all(lm[tip].y > lm[base].y for tip, base in [(8,5),(12,9),(16,13),(20,17)])

    def is_open_hand(self, lm):
        return all(lm[tip].y < lm[base].y for tip, base in [(8,5),(12,9),(16,13),(20,17)])