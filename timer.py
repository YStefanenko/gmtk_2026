import math
from opengl_manager import opengl_manager

ASPECT = 16 / 9
SEGMENTS = 64


class Timer:
    def __init__(self, value, index, position, size=0.15):
        self.value = value
        self.initial_value = value
        self.position = position
        self.size = size
        self.radius = size / 2 * 9 / 16

        self.index = index

        self.render_label()

    # -- label ----------------------------------------------------------
    def render_label(self):
        if f"timer_text_{self.index}" in opengl_manager.textures:
            opengl_manager.delete_image(f"timer_text_{self.index}")

        label_size = self.size * 864 * 0.7
        opengl_manager.load_text(str(self.value), (255, 255, 255), label_size, self.position, f"timer_text_{self.index}", outline=10)

    def tick(self):
        self.value -= 1
        self.render_label()

    def is_pressed(self, mouse):
        """True if `mouse` (0-1 screen coords) is inside the timer circle."""
        cx, cy = self.position
        rx = self.radius            # x-radius
        ry = self.radius * ASPECT   # y-radius (= size / 2)
        return ((mouse[0] - cx) / rx) ** 2 + ((mouse[1] - cy) / ry) ** 2 <= 1

    def arc(self, fraction):
        cx, cy = self.position
        points = [(cx, cy)]
        segments = max(1, int(round(SEGMENTS * fraction)))
        for i in range(segments + 1):
            angle = math.pi / 2 - 2 * math.pi * fraction * (i / segments)
            dx = math.cos(angle) * self.radius
            dy = math.sin(angle) * self.radius * ASPECT
            points.append((cx + dx, cy + dy))
        return points

    # -- render ---------------------------------------------------------
    def render(self, print_as_selected=False):
        opengl_manager.draw_lines(self.arc(1.0), (0.20, 0.21, 0.26, 1.0), 0)

        fraction = min(self.value, self.initial_value) / self.initial_value
        fraction = max(0.0, fraction)
        if fraction > 0:
            opengl_manager.draw_lines(self.arc(fraction), (0.90, 0.76, 0.25, 1.0), 0)

        if print_as_selected:
            opengl_manager.draw_lines(self.arc(1.0)[1:], (1, 1, 1, 1), 10, loop=True)

        opengl_manager.draw_text(f"timer_text_{self.index}")
