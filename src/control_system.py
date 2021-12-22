import pyautogui
import threading
from time import sleep
from math import sqrt


class SystemController:
    def __init__(self, cursor_speed=5000):
        size = pyautogui.size()
        self.width = size.width
        self.height = size.height
        self._control_thread = threading.Thread(target=self._control_loop)
        self._control_lock = threading.Lock()
        self._target_position = None
        self._quit = False
        self._cursor_speed = cursor_speed
        self._cursor_distance_per_tick = cursor_speed * 0.01
        self._queued_moves = []

        self._control_thread.start()

    def stop(self):
        self._quit = True
        if self._control_thread.is_alive():
            self._control_thread.join()

    def restart(self):
        self._quit = False
        self._control_thread = threading.Thread(target=self._control_loop)
        self._control_thread.start()

    def enqueue_move(self, target_position, move_time):
        self._control_lock.acquire()
        self._queued_moves.append((target_position, move_time))
        self._control_lock.release()

    def mouse_down(self):
        pyautogui.mouseDown(_pause=False)

    def mouse_up(self):
        pyautogui.mouseUp(_pause=False)

    def _control_loop(self):
        while not self._quit:
            next_move = None
            self._control_lock.acquire()
            if len(self._queued_moves) != 0:
                next_move = self._queued_moves.pop(0)
            self._control_lock.release()
            if next_move is None:
                sleep(0.001)
                continue
            target_position, move_time = next_move
            screen_position = target_position[0] * self.width, target_position[1] * self.height

            if move_time is None:
                pyautogui.moveTo(*screen_position)
                continue
            pyautogui.moveTo(*screen_position, move_time, _pause=False)
