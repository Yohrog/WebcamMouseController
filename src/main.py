from dataclasses import dataclass
import time
from math import sqrt

from hand_tracking import HandTracker
from control_system import SystemController
# from screen_overlay import ScreenInterface


@dataclass
class PointWithLifetime:
    x: int = 0
    y: int = 0
    lifetime: float = 0
    index: int = 0


def add_tuples(a, b):
    assert(len(a) == len(b))
    return (element_a + element_b for element_a, element_b in zip(a, b))


if __name__ == "__main__":
    hand_tracker = HandTracker()
    system_controller = SystemController()
    fps_samples = []
    last_frame_time = time.time()
    last_detection_time = time.time()
    tracking_lost = True
    jitter_threshold = 0.006
    precision_mode_threshold = 0.3
    precision_mode_factor = 0.3
    last_position = None
    click_trigger_threshold = 0.04
    click_release_threshold = 0.07
    is_clicked = False

    try:
        while True:
            hand_tracker.detect_hands()
            hand_tracker.show_debug_image()

            now = time.time()
            frame_time_delta = now - last_frame_time
            last_frame_time = now
            fps = 1 / frame_time_delta

            if len(fps_samples) < 30:
                fps_samples.append(fps)
            else:
                fps_samples.pop(0)
                fps_samples.append(fps)

            average_fps = 0
            for sample in fps_samples:
                average_fps += sample
            average_fps /= len(fps_samples)

            if hand_tracker.hands_detected:
                last_detection_time = now
                hands = hand_tracker.get_hands()
                hand = hands[0]

                thumb_tip = hand.thumb.tip
                thumb_position = [thumb_tip.x, thumb_tip.y, thumb_tip.z]
                middle_tip = hand.middle_finger.tip
                middle_position = [middle_tip.x, middle_tip.y, middle_tip.z]
                finger_distance = 0
                for thumb, middle in zip(thumb_position, middle_position):
                    finger_distance += (thumb - middle)**2
                finger_distance = sqrt(finger_distance)

                if is_clicked:
                    if finger_distance > click_release_threshold:
                        system_controller.mouse_up()
                        is_clicked = False
                else:
                    if finger_distance < click_trigger_threshold:
                        system_controller.mouse_down()
                        is_clicked = True

                index_position = (hand.index_finger.tip.x, hand.index_finger.tip.y)
                if last_position:
                    relative_vector = [index_position[0] - last_position[0], index_position[1] - last_position[1]]
                    move_distance = sqrt(relative_vector[0] ** 2 + relative_vector[1] ** 2)
                    if move_distance < jitter_threshold:
                        continue
                    if move_distance < precision_mode_threshold:
                        speed_factor = precision_mode_factor * move_distance / precision_mode_threshold
                        index_position = [last + relative * speed_factor for last, relative in zip(last_position, relative_vector)]

                last_position = index_position
                if tracking_lost:
                    system_controller.enqueue_move(index_position, None)
                    tracking_lost = False
                else:
                    system_controller.enqueue_move(index_position, frame_time_delta)
            else:
                if time.time() - last_detection_time > 0.5:
                    system_controller.stop()
                    system_controller.restart()
                    tracking_lost = True

    except KeyboardInterrupt:
        system_controller.stop()
