from opengl_manager import opengl_manager
import numpy as np
from sound_manager import sound_manager


class CountdownTile:
    def __init__(self, grid_position, position, size, value):
        self.position = position
        self.grid_position = np.array(grid_position)
        self.value = value
        self.become_a_wall = False
        self.size = size
        opengl_manager.load_text(str(self.value), (255, 255, 255), 24, self.position, f'ct{self.position}', outline=2)

    def tick(self):
        self.value -= 1

        if self.value == 0:
            self.become_a_wall = True
            sound_manager.play_effect('cdt_activate')
        else:
            opengl_manager.delete_image(f'ct{self.position}')
            opengl_manager.load_text(str(self.value), (255, 255, 255), 24, self.position, f'ct{self.position}', outline=2)
            sound_manager.play_effect('cdt_tick')

    def render(self):
        opengl_manager.draw_image('countdown_tile', self.position, self.size)
        opengl_manager.draw_text(f'ct{self.position}')
