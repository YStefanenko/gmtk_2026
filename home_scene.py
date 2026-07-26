import pygame
import numpy as np
from opengl_manager import opengl_manager
from overlay_manager import OVERLAY_ACTION
from levels import levels
from overlay_manager import overlay_manager
from resource import resource_path
from global_variables import get_levels_completed
from sound_manager import sound_manager


class HomeScene:
    def __init__(self):
        opengl_manager.clear_images()

        for asset in ['logo', 'level_box', 'level_box_selected', 'level_box_locked', 'play', 'play-hover', 'background', 'volume_icon', 'volume_slider', 'volume_slider_pip']:
            image = pygame.image.load(resource_path(f"assets/{asset}.png"))
            image = pygame.transform.scale_by(image, 4)
            opengl_manager.load_pygame_surface(f"{asset}", image)

        self.total_levels = 30
        self.cols = 6
        self.rows = 5

        self.level_box_size = (0.05, 0.05 * 16 / 9)

        self.bg_color = (0.271, 0.157, 0.235, 1)

        self.max_level = get_levels_completed() + 1
        self.selected = get_levels_completed() + 1

        self.change_scene = None
        self.next_level = self.selected

        self.hover_play = False

        self.boxes = []
        left_x = 0.12 + 0.2
        right_x = 0.88 - 0.2
        top_y = 0.70
        row_step = 0.10
        self.box_hw = 0.06
        self.box_hh = 0.042

        for level in sorted(int(k) for k in levels):
            slot = level - 1
            col = slot % self.cols
            row = slot // self.cols
            cx = left_x + (right_x - left_x) * col / (self.cols - 1)
            cy = top_y - row * row_step
            unlocked = level <= self.max_level
            self.boxes.append((level, cx, cy, unlocked))

        play_h = 0.16
        play_w = play_h * (56 / 24) * (9 / 16)
        self.play_size = (play_w, play_h)
        self.play_cx = 0.5
        self.play_cy = 0.13
        self.play_hw = play_w / 2
        self.play_hh = play_h / 2

        # Volume slider (bottom right)
        self.vol_y = 0.07
        slider_w = 0.13
        slider_h = slider_w / ((41 / 8) * (9 / 16))
        icon_h = 0.05
        icon_w = icon_h * ((11 / 14) * (9 / 16))
        pip_h = 0.032
        pip_w = pip_h * ((4 / 4) * (9 / 16))
        self.slider_size = (slider_w, slider_h)
        self.icon_size = (icon_w, icon_h)
        self.pip_size = (pip_w, pip_h)

        self.slider_cx = 0.90
        track_left = self.slider_cx - slider_w / 2
        track_right = self.slider_cx + slider_w / 2
        self.vol_x_min = track_left + pip_w / 2
        self.vol_x_max = track_right - pip_w / 2
        self.icon_cx = track_left - 0.02 - icon_w / 2

        self.vol_hit_hw = slider_w / 2 + pip_w / 2
        self.vol_hit_hh = 0.035

        self.volume = sound_manager.music_volume
        self.dragging = False

        for level, cx, cy, unlocked in self.boxes:
            color = (240, 235, 245) if unlocked else (150, 140, 150)
            opengl_manager.load_text(str(level), color, 34, (cx, cy), f'home_lvl_{level}')

        self.frame = 0

    def _hit(self, cx, cy, hw, hh, mouse):
        return cx - hw <= mouse[0] <= cx + hw and cy - hh <= mouse[1] <= cy + hh

    def _set_volume_from_mouse(self, mouse):
        span = self.vol_x_max - self.vol_x_min
        value = (mouse[0] - self.vol_x_min) / span if span else 0.0
        value = max(0.0, min(1.0, value))
        self.volume = value
        sound_manager.set_volume(value)

    def event_check(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                return 0

            elif event.type == OVERLAY_ACTION:
                return 0

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    overlay_manager.open_ec("close the game")

            elif event.type == pygame.MOUSEMOTION:
                mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
                self.hover_play = self._hit(self.play_cx, self.play_cy, self.play_hw, self.play_hh, mouse)
                if self.dragging:
                    self._set_volume_from_mouse(mouse)

            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
                if self._hit(self.slider_cx, self.vol_y, self.vol_hit_hw, self.vol_hit_hh, mouse):
                    self.dragging = True
                    self._set_volume_from_mouse(mouse)
                    return 1
                if self._hit(self.play_cx, self.play_cy, self.play_hw, self.play_hh, mouse):
                    self.next_level = self.selected
                    self.change_scene = 'game'
                    return 1
                for level, cx, cy, unlocked in self.boxes:
                    if unlocked and self._hit(cx, cy, self.box_hw, self.box_hh, mouse):
                        self.selected = level
                        self.next_level = level
                        self.change_scene = 'game'
                        return 1

        return 1

    def update(self):
        self.frame += 1

    def render(self):
        opengl_manager.clear_screen()
        # opengl_manager.draw_polygon([(0, 0), (1, 0), (1, 1), (0, 1)], self.bg_color)

        mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
        offset = np.array([0.5, 0.5]) - mouse
        opengl_manager.draw_image('background', np.array([0.5, 0.5]) + offset / 10, (1.1, 1.1))

        opengl_manager.draw_image('logo', (0.5, 0.85), (0.22 * 1.5, 0.109 * 1.5))

        for level, cx, cy, unlocked in self.boxes:
            if not unlocked:
                image = 'level_box_locked'
            elif level == self.selected:
                image = 'level_box_selected'
            else:
                image = 'level_box'
            opengl_manager.draw_image(image, (cx, cy), self.level_box_size)
            opengl_manager.draw_text(f'home_lvl_{level}')

        play_image = 'play-hover' if self.hover_play else 'play'
        opengl_manager.draw_image(play_image, (self.play_cx, self.play_cy), self.play_size)

        opengl_manager.draw_image('volume_icon', (self.icon_cx, self.vol_y), self.icon_size)
        opengl_manager.draw_image('volume_slider', (self.slider_cx, self.vol_y), self.slider_size)
        pip_x = self.vol_x_min + self.volume * (self.vol_x_max - self.vol_x_min)
        opengl_manager.draw_image('volume_slider_pip', (pip_x, self.vol_y), self.pip_size)
