from enum import Enum

import cv2
import mediapipe


class HandTracker:
    def __init__(self, camera=0):
        self.camera = cv2.VideoCapture(0)
        self.drawing_utils = mediapipe.solutions.drawing_utils
        self.hands_detected = False
        self.bgr_image = None
        self._results = None
        self._legacy_results = None
        self._hand_detector = mediapipe.solutions.hands.Hands(min_tracking_confidence=0.7)

    def detect_hands(self):
        success, self.bgr_image = self.camera.read()
        self.bgr_image = cv2.flip(self.bgr_image, 1)
        if not success:
            self.hands_detected = False
            return
        rgb_image = cv2.cvtColor(self.bgr_image, cv2.COLOR_BGR2RGB)

        self._results = self._hand_detector.process(rgb_image)

        if not self._results:
            self.hands_detected = False
            return

        if self._results.multi_hand_landmarks:
            self.hands_detected = True
        else:
            self.hands_detected = False

    def get_hands(self):
        if not self.hands_detected:
            return None

        hands = []
        for hand_landmarks in self._results.multi_hand_landmarks:
            landmarks = []
            for index, landmark in enumerate(hand_landmarks.landmark):
                landmarks.append(landmark)
            hands.append(Hand(landmarks))
        self._legacy_results = self._results
        self._results = None
        return hands

    def show_debug_image(self):
        if self.bgr_image is None:
            return
        if self._results:
            if self._results.multi_hand_landmarks:
                for hand_landmarks in self._results.multi_hand_landmarks:
                    self.drawing_utils.draw_landmarks(self.bgr_image, hand_landmarks, mediapipe.solutions.hands.HAND_CONNECTIONS)
        elif self._legacy_results:
            if self._legacy_results.multi_hand_landmarks:
                for hand_landmarks in self._legacy_results.multi_hand_landmarks:
                    self.drawing_utils.draw_landmarks(self.bgr_image, hand_landmarks, mediapipe.solutions.hands.HAND_CONNECTIONS)
        cv2.imshow("Hand Detection", self.bgr_image)
        cv2.waitKey(1)


class Hand:
    class Finger:
        class Segments(Enum):
            MCP = 0
            PIP = 1
            DIP = 2
            TIP = 3

        def __init__(self, segment_list):
            self.mcp = segment_list[0]
            self.pip = segment_list[1]
            self.dip = segment_list[2]
            self.tip = segment_list[3]
            self.segments = segment_list

        def __getitem__(self, item):
            return self.segments[item]

    class Thumb:
        class Segments(Enum):
            CMC = 0
            MCP = 1
            IP = 2
            TIP = 3

        def __init__(self, segment_list):
            self.cmc = segment_list[0]
            self.mcp = segment_list[1]
            self.ip = segment_list[2]
            self.tip = segment_list[3]
            self.segments = segment_list

        def __getitem__(self, item):
            return self.segments[item]

    def __init__(self, landmark_list):
        self.wrist = landmark_list[0]
        self.thumb = Hand.Thumb(landmark_list[1:5])
        self.index_finger = Hand.Finger(landmark_list[5:9])
        self.middle_finger = Hand.Finger(landmark_list[9:13])
        self.ring_finger = Hand.Finger(landmark_list[13:17])
        self.pinky_finger = Hand.Finger(landmark_list[17:21])
        self.landmarks = landmark_list

    def __getitem__(self, item):
        return self.landmarks[item]


if __name__ == "__main__":
    try:
        hand_tracker = HandTracker()
        while True:
            hand_tracker.detect_hands()
            hand_tracker.show_debug_image()

    except KeyboardInterrupt:
        pass
