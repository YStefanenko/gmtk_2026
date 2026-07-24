import math
from opengl_manager import opengl_manager


class Timer:
    def __init__(self, value, position, size):
        self.value = value
        self.initial_value = value
        self.position = position
        self.size = size

    def tick(self):
        self.value -= 1

    def is_pressed(self, mouse):
        if abs(mouse[0] - self.position[0]) < self.size[0] / 2 and abs(mouse[1] - self.position[1]) < self.size[1] / 2:
            return 1
        else:
            return 0


    def render(self, print_as_selected=False):
        opengl_manager.draw_image(("clock" + str(int(self.value)) + ("p" if print_as_selected else "")), self.position, self.size)
