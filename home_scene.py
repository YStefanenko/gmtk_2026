import pygame
import numpy as np
from opengl_manager import opengl_manager
from overlay_manager import OVERLAY_ACTION
from levels import levels
from overlay_manager import overlay_manager
from resource import resource_path


class HomeScene:
    def __init__(self):
        opengl_manager.clear_images()

        opengl_manager.load_image('logo', resource_path(f"assets/logo.png"))

        self.total_levels = 30
        self.cols = 6
        self.rows = 5

        self.bg_color = (0.271, 0.157, 0.235, 1)
        self.box_color = (0.40, 0.30, 0.45, 1)
        self.box_hover_color = (0.60, 0.45, 0.65, 1)
        self.box_disabled_color = (0.32, 0.22, 0.30, 1)
        self.outline_color = (0.85, 0.80, 0.85, 1)
        self.play_color = (0.95, 0.75, 0.20, 1)
        self.play_hover_color = (1.0, 0.85, 0.35, 1)

        self.available = {int(k) for k in levels}

        self.change_scene = None
        self.next_level = 1

        self.hover_level = None
        self.hover_play = False

        self.boxes = []
        left_x = 0.12
        right_x = 0.88
        top_y = 0.70
        row_step = 0.10
        self.box_hw = 0.06
        self.box_hh = 0.042

        for i in range(self.total_levels):
            col = i % self.cols
            row = i // self.cols
            cx = left_x + (right_x - left_x) * col / (self.cols - 1)
            cy = top_y - row * row_step
            level = i + 1
            enabled = level in self.available
            self.boxes.append((level, cx, cy, enabled))

        self.play_cx = 0.5
        self.play_cy = 0.13
        self.play_hw = 0.13
        self.play_hh = 0.055

        opengl_manager.load_text('PLAY', (40, 25, 35), 60, (self.play_cx, self.play_cy), 'home_play')

        for level, cx, cy, enabled in self.boxes:
            color = (240, 235, 245) if enabled else (150, 140, 150)
            opengl_manager.load_text(str(level), color, 34, (cx, cy), f'home_lvl_{level}')

    def _hit(self, cx, cy, hw, hh, mouse):
        return cx - hw <= mouse[0] <= cx + hw and cy - hh <= mouse[1] <= cy + hh

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
                self.hover_level = None
                for level, cx, cy, enabled in self.boxes:
                    if enabled and self._hit(cx, cy, self.box_hw, self.box_hh, mouse):
                        self.hover_level = level
                        break

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
                if self._hit(self.play_cx, self.play_cy, self.play_hw, self.play_hh, mouse):
                    self.next_level = 1
                    self.change_scene = 'game'
                    return 1
                for level, cx, cy, enabled in self.boxes:
                    if enabled and self._hit(cx, cy, self.box_hw, self.box_hh, mouse):
                        self.next_level = level
                        self.change_scene = 'game'
                        return 1

        return 1

    def update(self):
        pass

    def _draw_box(self, cx, cy, hw, hh, fill):
        corners = [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh)]
        opengl_manager.draw_polygon(corners, fill)
        opengl_manager.draw_lines(corners, self.outline_color, 2, loop=True)

    def render(self):
        opengl_manager.clear_screen()
        opengl_manager.draw_polygon([(0, 0), (1, 0), (1, 1), (0, 1)], self.bg_color)

        opengl_manager.draw_image('logo', (0.5, 0.9), (0.22 * 1.5, 0.109 * 1.5))

        for level, cx, cy, enabled in self.boxes:
            if not enabled:
                fill = self.box_disabled_color
            elif self.hover_level == level:
                fill = self.box_hover_color
            else:
                fill = self.box_color
            self._draw_box(cx, cy, self.box_hw, self.box_hh, fill)
            opengl_manager.draw_text(f'home_lvl_{level}')

        play_fill = self.play_hover_color if self.hover_play else self.play_color
        self._draw_box(self.play_cx, self.play_cy, self.play_hw, self.play_hh, play_fill)
        opengl_manager.draw_text('home_play')
