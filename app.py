import os
import sys
def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel)
os.chdir(os.path.dirname(sys.argv[0]))
if sys.platform == "darwin":
    os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
else:
    os.environ["SDL_VIDEO_WINDOW_POS"] = "100,100"
os.environ["SDL_VIDEO_CENTERED"] = "0"
os.environ["SDL_VIDEO_ALLOW_SCREENSAVER"] = "1"
os.environ["SDL_VIDEO_HIGHDPI_DISABLED"] = "1"
import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
import math
levels_completed = 0
def get_levels_completed():
    return levels_completed
def set_levels_completed(value):
    global levels_completed
    levels_completed = value
class GameScene:
    def __init__(self, level):
        opengl_manager.clear_images()
        sound_manager.play_music('game')
        image = pygame.image.load(resource_path(f"assets/background2.png"))
        image = pygame.transform.scale_by(image, 4)
        opengl_manager.load_pygame_surface(f"background", image)
        for asset in ['back_to_menu', 'back_to_menu_hover', 'level_complete', 'level_failed', 'try_again', 'try_again_hover', 'next_level', 'next_level_hover', 'restart', 'restart_hover', 'hint1', 'hint2', 'hint3']:
            image = pygame.image.load(resource_path(f"assets/{asset}.png"))
            image = pygame.transform.scale_by(image, 4)
            opengl_manager.load_pygame_surface(f"{asset}", image)
        for asset in ['tick', 'cross', 'finish_tile', 'countdown_tile', 'outerwall0', 'outerwall1', 'outerwall3', 'outerwall4', 'player_shadow', 'green_up', 'green_down', 'green_left', 'green_right', 'red_up', 'red_down', 'red_left', 'red_right']:
            image = pygame.image.load(resource_path(f"assets/{asset}.png"))
            image = pygame.transform.scale(image, (96, 96))
            opengl_manager.load_pygame_surface(asset, image)
        for name in ['tbar', 'ybar', 'bbar']:
            for i in range(1, 7):
                image = pygame.image.load(resource_path(f"assets/{name}{i}.png"))
                image = pygame.transform.scale(image, (96, 96))
                opengl_manager.load_pygame_surface(f"{name}{i}", image)
        for i in range(0, 11):
            image = pygame.image.load(resource_path(f"assets/clock{i}.png"))
            image = pygame.transform.scale(image, (96, 96))
            opengl_manager.load_pygame_surface(f"clock{i}", image)
        for i in range(0, 11):
            image = pygame.image.load(resource_path(f"assets/clock{i}p.png"))
            image = pygame.transform.scale(image, (96, 96))
            opengl_manager.load_pygame_surface(f"clock{i}p", image)
        for i in range(0, 10):
            image = pygame.image.load(resource_path(f"assets/lfloor{i}.png"))
            image = pygame.transform.scale(image, (96, 96))
            opengl_manager.load_pygame_surface(f"lfloor{i}", image)
        for i in range(0, 10):
            image = pygame.image.load(resource_path(f"assets/dfloor{i}.png"))
            image = pygame.transform.scale(image, (96, 96))
            opengl_manager.load_pygame_surface(f"dfloor{i}", image)
        for i in range(0, 22):
            if i == 17 or i == 20:
                continue
            image = pygame.image.load(resource_path(f"assets/wall{i}.png"))
            image = pygame.transform.scale(image, (96, 96))
            opengl_manager.load_pygame_surface(f"wall{i}", image)
        for i in range(0, 4):
            image = pygame.image.load(resource_path(f"assets/top{i}.png"))
            image = pygame.transform.scale(image, (96, 96))
            opengl_manager.load_pygame_surface(f"top{i}", image)
        for i in range(1, 25):
            image = pygame.image.load(resource_path(f"assets/mouse{i}.png"))
            image = pygame.transform.scale(image, (128, 128))
            opengl_manager.load_pygame_surface(f"mouse{i}", image)
        self.level = np.array(levels[str(level)]['grid'][::-1])
        self.start = np.where(self.level == 2)
        self.start = (self.start[1][0], self.start[0][0])
        self.level[self.start[1], self.start[0]] = 0
        self.finish = np.where(self.level == 3)
        self.finish = (self.finish[1][0], self.finish[0][0])
        self.level[self.finish[1], self.finish[0]] = 0
        self.cell_w = self.cell_h = self.offset_x = self.offset_y = 0
        self.calculate_grid()
        self.countdown_tiles = np.where(self.level == 4)
        for i in range(len(self.countdown_tiles[0])):
            self.level[self.countdown_tiles[0][i], self.countdown_tiles[1][i]] = 0
        self.countdown_tiles_values = levels[str(level)].get('countdown_tiles', [])
        if len(self.countdown_tiles_values) < len(self.countdown_tiles[0]):
            self.countdown_tiles_values = self.countdown_tiles_values + [5] * (len(self.countdown_tiles[0]) - len(self.countdown_tiles_values))
        self.countdown_tiles = [CountdownTile((self.countdown_tiles[1][i], self.countdown_tiles[0][i]), self.grid_to_screen((self.countdown_tiles[1][i] + 0.5, self.countdown_tiles[0][i] + 0.5)), (self.cell_w, self.cell_h), self.countdown_tiles_values[i]) for i in range(len(self.countdown_tiles[0]))]
        self.player = Player(self.start, self)
        self.selected_timer = 0
        timer_values = levels[str(level)]['timers']
        centre_x = 0.5
        timer_y = self.grid_to_screen((0, self.level.shape[1] + 3))[1]
        n = len(timer_values)
        spacing = self.cell_w * 1.5
        left_x = centre_x - (n - 1) * spacing / 2
        self.timers = [Timer(value, (left_x + i * spacing, timer_y), (self.cell_w * 2, self.cell_h * 2)) for i, value in enumerate(timer_values)]
        self.player.speed = self.timers[self.selected_timer].value
        self.game = True
        self.current_level = level
        self.next_level = level
        self.change_scene = None
        self.end_buttons = []
        self.end_title = None
        self.end_title_size = (0.96 * 9 / 16, 0.96)
        self.end_button_size = (0.4 * 9 / 16, 0.4 / 128 * 36)
        self.end_button_hw = self.end_button_size[0] / 2
        self.end_button_hh = self.end_button_size[1] / 2
        self.hover_button = None
        restart_h = 0.2
        restart_w = restart_h * (38 / 40) * (9 / 16)
        self.restart_size = (restart_w, restart_h)
        self.restart_cx = 0.95
        self.restart_cy = 0.92
        self.restart_hw = restart_w / 2
        self.restart_hh = restart_h / 2
        self.hover_restart = False
        hint_px = {'hint1': (134, 92), 'hint2': (134, 106), 'hint3': (154, 82)}
        hint_levels = {1: ['hint1', 'hint2'], 2: ['hint1', 'hint2'], 13: ['hint3'], 14: ['hint3']}
        hint_w = 0.14
        left_x = 0.12
        top_y = 0.65
        gap = 0.02
        self.hints = []
        for name in hint_levels.get(level, []):
            w_px, h_px = hint_px[name]
            hint_h = hint_w * (h_px / w_px) * (16 / 9)
            cx = left_x + hint_w / 2
            cy = top_y - hint_h / 2
            self.hints.append((name, (cx, cy), (hint_w, hint_h)))
            top_y -= hint_h + gap
    def calculate_grid(self):
        rows, cols = self.level.shape
        rows += 5
        cols += 2
        self.cell_h = min(0.95 / rows, 0.9 * 16 / 9 / cols)
        self.cell_w = self.cell_h * 9 / 16
        self.offset_x = (1 - cols * self.cell_w) / 2
        self.offset_y = (1 - rows * self.cell_h) / 2
        self.offset_x += self.cell_w
        self.offset_y += self.cell_h
    def grid_to_screen(self, grid_pos):
        """Grid cell corner (col, row) -> screen coordinate (x, y)."""
        x = self.offset_x + grid_pos[0] * self.cell_w
        y = self.offset_y + grid_pos[1] * self.cell_h
        return x, y
    def screen_to_grid(self, screen_pos):
        """Screen coordinate (x, y) -> grid cell index (col, row)."""
        col = int((screen_pos[0] - self.offset_x) // self.cell_w)
        row = int((screen_pos[1] - self.offset_y) // self.cell_h)
        return col, row
    def event_check(self, events):
        if self.game:
            if self.player.position[0] == self.finish[0] and self.player.position[1] == self.finish[1]:
                self.end_level(1)
            else:
                if self.player.new_position is None:
                    total_timer = sum(timer.value for timer in self.timers)
                    if total_timer == 0:
                        self.end_level(0)
        for event in events:
            if event.type == pygame.QUIT:
                return 0
            elif event.type == OVERLAY_ACTION:
                self.change_scene = 'home'
                if self.game:
                    self.end_level(0)
                return 1
            elif not self.game:
                if event.type == pygame.MOUSEMOTION:
                    mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
                    self.hover_button = None
                    for action, cx, cy, name in self.end_buttons:
                        if self._hit(cx, cy, self.end_button_hw, self.end_button_hh, mouse):
                            self.hover_button = action
                            break
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
                    for action, cx, cy, name in self.end_buttons:
                        if self._hit(cx, cy, self.end_button_hw, self.end_button_hh, mouse):
                            if action == 'menu':
                                self.change_scene = 'home'
                            elif action == 'next':
                                self.next_level = self.current_level + 1
                                if str(self.next_level) in levels:
                                    self.change_scene = 'game'
                                else:
                                    self.change_scene = 'home'
                            elif action == 'retry':
                                self.next_level = self.current_level
                                self.change_scene = 'game'
                            break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        overlay_manager.open_ec("return to menu")
            elif event.type == pygame.MOUSEMOTION:
                mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
                self.hover_restart = self._hit(self.restart_cx, self.restart_cy, self.restart_hw, self.restart_hh, mouse)
                over_grid = (self.offset_x <= mouse[0] <= 1 - self.offset_x and self.offset_y <= mouse[1] <= 1 - self.offset_y)
                if over_grid and self.player.new_position is None:
                    self.player.update_move_suggestion(mouse)
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.select_timer(self.selected_timer - 1)
                elif event.y < 0:
                    self.select_timer(self.selected_timer + 1)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button != 1:
                    continue
                mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
                if self._hit(self.restart_cx, self.restart_cy, self.restart_hw, self.restart_hh, mouse):
                    self.next_level = self.current_level
                    self.change_scene = 'game'
                    return 1
                for i in range(len(self.timers)):
                    if self.timers[i].is_pressed(mouse):
                        self.select_timer(i)
                        break
                else:
                    self.do_move()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    overlay_manager.open_ec("return to menu")
                elif event.key == pygame.K_q:
                    self.select_timer(self.selected_timer - 1)
                elif event.key == pygame.K_e:
                    self.select_timer(self.selected_timer + 1)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.do_move()
                elif event.key in (pygame.K_w, pygame.K_UP):
                    self.do_move(np.array((0, 1)))
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    self.do_move(np.array((0, -1)))
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    self.do_move(np.array((-1, 0)))
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.do_move(np.array((1, 0)))
                elif event.key == pygame.K_r:
                    self.next_level = self.current_level
                    self.change_scene = 'game'
        return 1
    def select_timer(self, index):
        if 0 <= index < len(self.timers):
            self.selected_timer = index
            self.player.speed = self.timers[self.selected_timer].value
            self.player.update_move_suggestion()
    def update(self):
        self.player.update(self.countdown_tiles)
        for i in range(len(self.countdown_tiles)-1, -1, -1):
            if self.countdown_tiles[i].become_a_wall:
                self.level[self.countdown_tiles[i].grid_position[1], self.countdown_tiles[i].grid_position[0]] = 1
                self.countdown_tiles.pop(i)
        sound_manager.update_ticking(self.game)
    def render(self):
        opengl_manager.clear_screen()
        mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
        offset = np.array([0.5, 0.5]) - mouse
        opengl_manager.draw_image('background', np.array([0.5, 0.5]) + offset / 10, (1.1, 1.1))
        rows, cols = self.level.shape
        for r in range(rows-1, -1, -1):
            for c in range(cols):
                position = self.grid_to_screen((c + 0.5, r + 0.5))
                if self.level[r][c] == 0:
                    if (r + c) % 2 == 0:
                        costume = f"lfloor"
                    else:
                        costume = f"dfloor"
                    if r == 0:
                        if c == 0:
                            costume += "1"
                        elif c == cols - 1:
                            costume += "3"
                        else:
                            costume += "2"
                    elif r == rows - 1:
                        if c == 0:
                            costume += "7"
                        elif c == cols - 1:
                            costume += "9"
                        else:
                            costume += "8"
                    elif c == 0:
                        costume += "4"
                    elif c == cols - 1:
                        costume += "6"
                    else:
                        costume += "5"
                    opengl_manager.draw_image(costume, position, (self.cell_w, -self.cell_h))
        for tile in self.countdown_tiles:
            tile.render()
        opengl_manager.draw_image('finish_tile', self.grid_to_screen(self.finish + np.array([0.5, 0.5])), (self.cell_w, -self.cell_h))
        for c in range(cols):
            position = self.grid_to_screen((c + 0.5, -0.5))
            if c % 2 == 0:
                costume = f"lfloor0"
            else:
                costume = f"dfloor0"
            opengl_manager.draw_image(costume, position, (self.cell_w, self.cell_h))
            position = self.grid_to_screen((c + 0.5, rows + 0.5))
            if c % 3 == 0:
                costume = f"tbar"
            elif c % 3 == 1:
                costume = f"bbar"
            else:
                costume = f"ybar"
            if c == 0:
                costume += "4"
            elif c == cols - 1:
                costume += "6"
            else:
                costume += "5"
            opengl_manager.draw_image(costume, position, (self.cell_w, self.cell_h))
            position = self.grid_to_screen((c + 0.5, rows + 1.5))
            if c % 3 == 0:
                costume = f"tbar"
            elif c % 3 == 1:
                costume = f"bbar"
            else:
                costume = f"ybar"
            if c == 0:
                costume += "1"
            elif c == cols - 1:
                costume += "3"
            else:
                costume += "2"
            opengl_manager.draw_image(costume, position, (self.cell_w, self.cell_h))
        self.player.render_move_suggestion()
        self.player.render()
        opengl_manager.draw_image('outerwall0', self.grid_to_screen((-0.5, -0.5)), (self.cell_w, self.cell_h))
        opengl_manager.draw_image('outerwall0', self.grid_to_screen((cols + 0.5, -0.5)), (self.cell_w, self.cell_h))
        opengl_manager.draw_image('outerwall1', self.grid_to_screen((-0.5, 0.5)), (self.cell_w, self.cell_h))
        opengl_manager.draw_image('outerwall1', self.grid_to_screen((cols + 0.5, 0.5)), (self.cell_w, self.cell_h))
        for r in range(1, rows+1):
            opengl_manager.draw_image('wall11', self.grid_to_screen((-0.5, r + 0.5)), (self.cell_w, self.cell_h))
            opengl_manager.draw_image('wall11', self.grid_to_screen((cols + 0.5, r + 0.5)), (self.cell_w, self.cell_h))
        opengl_manager.draw_image('outerwall3', self.grid_to_screen((-0.5, rows + 1.5)), (self.cell_w, self.cell_h))
        opengl_manager.draw_image('outerwall4', self.grid_to_screen((cols + 0.5, rows + 1.5)), (self.cell_w, self.cell_h))
        for r in range(rows-1, -1, -1):
            for c in range(cols):
                position = self.grid_to_screen((c + 0.5, r + 0.5))
                if self.level[r][c] == 1:
                    costume = f"wall"
                    neighbours = self.get_neighbourhood(r, c)
                    if neighbours[1] == 1:
                        if neighbours[3] == 1:
                            if neighbours[5] == 1:
                                if neighbours[0] == 1:
                                    if neighbours[2] == 1:
                                        costume += "5"
                                    else:
                                        costume += "12"
                                else:
                                    if neighbours[2] == 1:
                                        costume += "10"
                                    else:
                                        costume += "14"
                            else:
                                if neighbours[0] == 1:
                                    if neighbours[2] == 1:
                                        costume += "6"
                                    else:
                                        costume += "9"
                                else:
                                    if neighbours[2] == 1:
                                        costume += "19"
                                    else:
                                        costume += "15"
                        else:
                            if neighbours[5] == 1:
                                if neighbours[0] == 1:
                                    if neighbours[2] == 1:
                                        costume += "4"
                                    else:
                                        costume += "21"
                                else:
                                    if neighbours[2] == 1:
                                        costume += "7"
                                    else:
                                        costume += "13"
                            else:
                                if neighbours[0] == 1:
                                    if neighbours[2] == 1:
                                        costume += "8"
                                    else:
                                        costume += "18"
                                else:
                                    if neighbours[2] == 1:
                                        costume += "16"
                                    else:
                                        costume += "11"
                    else:
                        if neighbours[3] == 1:
                            if neighbours[5] == 1:
                                costume += "2"
                            else:
                                costume += "3"
                        elif neighbours[5] == 1:
                            costume += "1"
                        else:
                            costume += "0"
                    opengl_manager.draw_image(costume, position, (self.cell_w, self.cell_h))
        for r in range(rows-1, -1, -1):
            for c in range(cols):
                position = self.grid_to_screen((c + 0.5, r + 1.5))
                if self.level[r][c] == 1 and (r == rows - 1 or self.level[r+1][c] == 0):
                    costume = f"top"
                    if c != 0 and self.level[r][c-1] == 1:
                        if c < cols - 1 and self.level[r][c + 1] == 1:
                            costume += "2"
                        else:
                            costume += "3"
                    elif c < cols - 1 and self.level[r][c+1] == 1:
                        costume += "1"
                    else:
                        costume += "0"
                    opengl_manager.draw_image(costume, position, (self.cell_w, self.cell_h))
        for i in range(len(self.timers)):
            self.timers[i].render(print_as_selected=(i == self.selected_timer))
        if self.game:
            restart_image = 'restart_hover' if self.hover_restart else 'restart'
            opengl_manager.draw_image(restart_image, (self.restart_cx, self.restart_cy), self.restart_size)
            for name, pos, size in self.hints:
                opengl_manager.draw_image(name, pos, size)
        if not self.game:
            opengl_manager.draw_image(self.end_title, (0.5, 0.55), self.end_title_size)
            for action, cx, cy, image in self.end_buttons:
                opengl_manager.draw_image(image + ("_hover" if self.hover_button == action else ""), (cx, cy), self.end_button_size)
    def get_neighbourhood(self, r, c):
        rows, cols = len(self.level), len(self.level[0])
        out = []
        for rr in (r - 1, r, r + 1):
            for cc in (c - 1, c, c + 1):
                if not (0 <= cc < cols):
                    out.append(0)
                elif not (0 <= rr < rows):
                    out.append(0)
                else:
                    out.append(self.level[rr][cc])
        return out
    def _hit(self, cx, cy, hw, hh, mouse):
        return cx - hw <= mouse[0] <= cx + hw and cy - hh <= mouse[1] <= cy + hh
    def end_level(self, result):
        self.game = False
        self.hover_button = None
        sound_manager.play_effect('windup')
        cy = 0.30
        left_cx = 0.5 - 0.1
        right_cx = 0.5 + 0.12
        if result:
            set_levels_completed(max(self.current_level, get_levels_completed()))
            sound_manager.play_effect('victory')
            self.end_title = 'level_complete'
            right_action, right_image = 'next', 'next_level'
        else:
            sound_manager.play_effect('defeat')
            self.end_title = 'level_failed'
            right_action, right_image = 'retry', 'try_again'
        self.end_buttons = [
            ('menu', left_cx, cy, 'back_to_menu'),
            (right_action, right_cx, cy, right_image),
        ]
    def do_move(self, direction=None):
        if self.player.speed <= 0:
            return
        moved = self.player.move(direction)
        if moved:
            self.timers[self.selected_timer].tick()
            self.player.speed = self.timers[self.selected_timer].value
            sound_manager.play_move()
class HomeScene:
    def __init__(self):
        opengl_manager.clear_images()
        sound_manager.play_music('menu')
        for asset in ['logo', 'level_box', 'level_box_selected', 'level_box_locked', 'play', 'play-hover', 'background', 'volume_icon', 'volume_slider', 'volume_slider_pip']:
            image = pygame.image.load(resource_path(f"assets/{asset}.png"))
            image = pygame.transform.scale_by(image, 4)
            opengl_manager.load_pygame_surface(f"{asset}", image)
        self.total_levels = 30
        self.cols = 6
        self.rows = 5
        self.level_box_size = (0.05, 0.05 * 16 / 9)
        self.bg_color = (0.271, 0.157, 0.235, 1)
        level_numbers = sorted(int(k) for k in levels)
        self.next_to_complete = get_levels_completed() + 1
        if self.next_to_complete not in level_numbers:
            self.next_to_complete = level_numbers[-1]
        self.selected = self.next_to_complete
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
        for level in level_numbers:
            slot = level - 1
            col = slot % self.cols
            row = slot // self.cols
            cx = left_x + (right_x - left_x) * col / (self.cols - 1)
            cy = top_y - row * row_step
            self.boxes.append((level, cx, cy))
        play_h = 0.16
        play_w = play_h * (56 / 24) * (9 / 16)
        self.play_size = (play_w, play_h)
        self.play_cx = 0.5
        self.play_cy = 0.13
        self.play_hw = play_w / 2
        self.play_hh = play_h / 2
        self.vol_y = 0.07
        slider_w = 0.13
        slider_h = slider_w / ((41 / 8) * (9 / 16))
        icon_h = 0.08
        icon_w = icon_h * ((11 / 14) * (9 / 16))
        pip_h = 0.022
        pip_w = pip_h * ((4 / 4) * (9 / 16))
        self.slider_size = (slider_w, slider_h)
        self.icon_size = (icon_w, icon_h)
        self.pip_size = (pip_w, pip_h)
        self.slider_cx = 0.90
        track_left = self.slider_cx - slider_w / 2 + 0.008
        track_right = self.slider_cx + slider_w / 2 - 0.008
        self.vol_x_min = track_left + pip_w / 2
        self.vol_x_max = track_right - pip_w / 2
        self.icon_cx = track_left - 0.02 - icon_w / 2
        self.vol_hit_hw = slider_w / 2 + pip_w / 2
        self.vol_hit_hh = 0.035
        self.volume = sound_manager.music_volume
        self.dragging = False
        for level, cx, cy in self.boxes:
            opengl_manager.load_text(str(level), (240, 235, 245), 34, (cx, cy), f'home_lvl_{level}')
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
                for level, cx, cy in self.boxes:
                    if self._hit(cx, cy, self.box_hw, self.box_hh, mouse):
                        self.selected = level
                        self.next_level = level
                        self.change_scene = 'game'
                        return 1
        return 1
    def update(self):
        self.frame += 1
    def render(self):
        opengl_manager.clear_screen()
        mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
        offset = np.array([0.5, 0.5]) - mouse
        opengl_manager.draw_image('background', np.array([0.5, 0.5]) + offset / 10, (1.1, 1.1))
        opengl_manager.draw_image('logo', (0.5, 0.85), (0.22 * 1.5, 0.109 * 1.5))
        for level, cx, cy in self.boxes:
            image = 'level_box_selected' if level == self.selected else 'level_box'
            opengl_manager.draw_image(image, (cx, cy), self.level_box_size)
            opengl_manager.draw_text(f'home_lvl_{level}')
        play_image = 'play-hover' if self.hover_play else 'play'
        opengl_manager.draw_image(play_image, (self.play_cx, self.play_cy), self.play_size)
        opengl_manager.draw_image('volume_icon', (self.icon_cx, self.vol_y), self.icon_size)
        opengl_manager.draw_image('volume_slider', (self.slider_cx, self.vol_y), self.slider_size)
        pip_x = self.vol_x_min + self.volume * (self.vol_x_max - self.vol_x_min)
        opengl_manager.draw_image('volume_slider_pip', (pip_x, self.vol_y), self.pip_size)
levels = {
'1': {'timers': [6],
'countdown_tiles': [],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 2, 0, 0, 3, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'2': {'timers': [8],
'countdown_tiles': [],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 1, 0, 1, 1, 1, 1, 1, 0, 1],
[1, 1, 0, 1, 0, 0, 0, 1, 0, 1],
[1, 1, 0, 1, 3, 1, 0, 1, 0, 1],
[1, 1, 0, 1, 1, 1, 0, 1, 0, 1],
[1, 1, 0, 0, 0, 0, 0, 1, 0, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
[2, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'3': {'timers': [8],
'countdown_tiles': [],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 2, 0, 0, 0, 0, 0, 0, 0, 0],
[1, 0, 1, 1, 0, 0, 0, 0, 0, 0],
[1, 0, 1, 0, 0, 1, 1, 1, 1, 0],
[1, 0, 0, 0, 0, 0, 0, 0, 1, 0],
[1, 0, 0, 1, 0, 1, 0, 0, 1, 0],
[1, 0, 0, 1, 0, 0, 0, 0, 1, 0],
[1, 0, 0, 1, 0, 0, 0, 0, 0, 0],
[1, 0, 0, 1, 1, 1, 1, 0, 3, 0],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]},
'4': {'timers': [8],
'countdown_tiles': [],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 1, 0, 1, 1, 1, 1, 1, 0, 1],
[1, 1, 0, 0, 0, 0, 0, 1, 0, 1],
[1, 1, 0, 0, 3, 1, 1, 1, 0, 1],
[1, 1, 0, 0, 1, 1, 0, 1, 0, 1],
[1, 1, 0, 0, 0, 0, 0, 1, 0, 1],
[1, 1, 1, 0, 0, 0, 0, 0, 0, 1],
[2, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'5': {'timers': [8],
'countdown_tiles': [],
'grid': [
[2, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
[0, 0, 1, 1, 0, 1, 1, 0, 0, 1],
[0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
[0, 0, 0, 0, 3, 0, 0, 0, 0, 1],
[0, 1, 1, 0, 0, 0, 1, 0, 0, 1],
[0, 0, 1, 0, 0, 1, 1, 0, 0, 1],
[0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'6': {'timers': [8],
'countdown_tiles': [],
'grid': [
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
[0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
[0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
[0, 0, 0, 0, 3, 1, 0, 0, 1, 1],
[0, 0, 0, 0, 1, 1, 0, 0, 1, 1],
[0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
[0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
[0, 0, 0, 1, 1, 1, 1, 1, 1, 1],
[0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'7': {'timers': [6],
'countdown_tiles': [2],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 0, 1, 1, 0, 1, 1, 1],
[1, 1, 1, 0, 1, 1, 0, 1, 1, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 2, 0, 0, 3, 4, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'8': {'timers': [5],
'countdown_tiles': [1, 1, 1, 1],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 0, 2, 0, 0, 0, 4, 0, 0, 1],
[1, 0, 0, 0, 3, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 4, 0, 0, 4, 0, 1],
[1, 0, 0, 0, 0, 4, 0, 0, 0, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'9': {'timers': [6],
'countdown_tiles': [1],
'grid': [
[1, 1, 1, 1, 0, 0, 0, 0, 1, 1],
[1, 2, 0, 0, 3, 0, 4, 0, 1, 1],
[1, 0, 1, 1, 1, 1, 0, 0, 1, 1],
[1, 0, 1, 1, 1, 1, 0, 0, 1, 1],
[1, 0, 1, 1, 1, 1, 0, 0, 1, 1],
[1, 0, 1, 1, 1, 1, 0, 0, 1, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 1, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'10': {'timers': [6],
'countdown_tiles': [1, 1],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 0, 0, 0, 0, 0, 0, 1, 1],
[1, 0, 2, 0, 0, 3, 0, 4, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 4, 0, 0, 0, 0, 0, 1, 1],
[1, 1, 0, 0, 0, 0, 0, 0, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'11': {'timers': [6],
'countdown_tiles': [1, 1],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
[1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
[1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
[1, 1, 1, 1, 1, 0, 0, 1, 0, 0],
[1, 1, 2, 0, 0, 3, 0, 4, 0, 0],
[1, 1, 0, 0, 0, 0, 0, 4, 0, 0],
[1, 1, 1, 1, 1, 0, 0, 1, 0, 0],
[1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
[1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
[1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
]},
'12': {'timers': [8],
'countdown_tiles': [1, 1],
'grid': [
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
[0, 2, 0, 0, 0, 0, 0, 4, 0, 0],
[0, 0, 3, 0, 1, 1, 1, 1, 0, 0],
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
[0, 0, 1, 0, 0, 0, 1, 1, 0, 0],
[0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
[0, 0, 1, 0, 1, 0, 1, 1, 0, 0],
[0, 4, 1, 0, 1, 0, 1, 1, 0, 0],
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]},
'13': {'timers': [6],
'countdown_tiles': [1, 1, 1, 1],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 0, 0, 1, 1, 1, 1, 0, 0, 1],
[1, 0, 0, 1, 1, 1, 1, 0, 0, 1],
[1, 0, 0, 0, 1, 1, 0, 0, 0, 1],
[1, 0, 0, 0, 1, 1, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 4, 0, 0, 0, 1],
[1, 0, 2, 0, 4, 3, 4, 0, 0, 1],
[1, 1, 0, 0, 0, 4, 0, 0, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'14': {'timers': [3, 2, 1],
'countdown_tiles': [],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[2, 0, 0, 0, 0, 0, 0, 0, 1, 1],
[1, 1, 0, 0, 0, 0, 0, 0, 0, 3],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'15': {'timers': [4, 3, 2, 1],
'countdown_tiles': [],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 1, 1, 0, 0, 0, 0, 1],
[1, 0, 1, 1, 1, 1, 1, 0, 0, 1],
[1, 0, 0, 0, 3, 1, 1, 0, 0, 1],
[1, 0, 0, 1, 1, 2, 0, 0, 0, 1],
[1, 0, 0, 1, 1, 1, 1, 1, 0, 1],
[1, 0, 0, 0, 0, 1, 1, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'16': {'timers': [5, 4, 3, 2, 1],
'countdown_tiles': [],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 3, 0, 0, 0, 0, 0, 0, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 0, 1, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 1, 1],
[1, 0, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
[2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]},
'17': {'timers': [5, 4, 3, 2, 1],
'countdown_tiles': [],
'grid': [
[0, 0, 0, 1, 1, 1, 1, 1, 1, 1],
[0, 1, 0, 1, 1, 1, 1, 1, 1, 1],
[0, 1, 0, 1, 0, 0, 0, 1, 1, 1],
[0, 1, 0, 1, 0, 1, 0, 1, 1, 1],
[0, 1, 0, 1, 0, 1, 0, 1, 1, 1],
[0, 1, 0, 1, 0, 1, 0, 0, 1, 1],
[0, 1, 0, 1, 0, 1, 1, 0, 3, 1],
[0, 1, 0, 1, 0, 1, 1, 1, 1, 1],
[0, 1, 0, 0, 0, 1, 1, 1, 1, 1],
[2, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'18': {'timers': [4, 3, 2],
'countdown_tiles': [],
'grid': [
[0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
[0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
[0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
[0, 0, 0, 2, 1, 1, 3, 0, 0, 0],
[0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
[0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
[0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'19': {'timers': [6, 6],
'countdown_tiles': [1, 1, 1, 1],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 2, 3, 1, 1, 1, 1],
[0, 0, 0, 1, 0, 0, 1, 0, 0, 0],
[0, 0, 0, 4, 0, 0, 4, 0, 0, 0],
[0, 1, 1, 1, 4, 4, 1, 1, 1, 0],
[0, 1, 1, 1, 0, 0, 1, 1, 1, 0],
[0, 1, 1, 1, 0, 0, 1, 1, 1, 0],
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]},
'20': {'timers': [3, 3, 3],
'countdown_tiles': [2],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 0, 0, 2, 1, 1, 1, 1, 1],
[1, 1, 0, 1, 0, 1, 1, 3, 1, 1],
[1, 1, 0, 1, 0, 1, 0, 0, 1, 1],
[1, 1, 0, 0, 4, 0, 0, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'21': {'timers': [4, 4, 4],
'countdown_tiles': [2, 5],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 0, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 4, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 0, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 0, 1, 1, 1, 0, 3, 1],
[1, 1, 0, 2, 0, 0, 4, 0, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]},
'22': {'timers': [6, 4, 4],
'countdown_tiles': [1],
'grid': [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 2, 0, 0, 0, 4, 1, 1, 1, 1],
[1, 0, 1, 1, 1, 0, 1, 1, 1, 1],
[1, 0, 1, 0, 0, 0, 1, 1, 1, 1],
[1, 0, 1, 1, 0, 1, 1, 1, 1, 1],
[1, 0, 1, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 1, 0, 0, 0, 0, 3, 0, 1],
[1, 0, 1, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
]},
}
class OpenglManager:
    def __init__(self):
        self.map_size = np.array([1600, 900])
        self.inv_map_size = np.array([1600, -900])
        self.screen_size = np.array([0, 0])
        self.screen_offset = np.array([0, 0])
        self.shaders = []
        self.shader_buffer = None
        self.shader_buffer_texture = None
        self.shader_number = 0
        self.control_text = "TeaAndPython's secret text (don't even dare read this)"
        self.reference_width = 1979
        self.textures = {}
        self.rendered_text = {}
    def create_screen(self):
        pygame.display.gl_set_attribute(pygame.GL_ACCELERATED_VISUAL, 1)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        if sys.platform == "darwin":
            info = pygame.display.Info()
            size = (info.current_w, info.current_h)
        else:
            size = (0, 0)
        pygame.display.set_mode(size, pygame.OPENGL | pygame.DOUBLEBUF | pygame.NOFRAME, vsync=1)
        screen = pygame.display.get_surface()
        win_w, win_h = screen.get_size()
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
        if sys.platform == "darwin":
            fb_w, _ = pygame.display.get_window_size()
            raw_scale = fb_w / win_w if win_w else 1.0
            self.pixel_scale = 2.0 if raw_scale >= 1.9 else 1.0
        else:
            self.pixel_scale = 1.0
        screen_aspect = win_w / win_h
        target_aspect = 16 / 9
        if screen_aspect >= target_aspect:
            view_h = win_h
            view_w = int(view_h * target_aspect)
        else:
            view_w = win_w
            view_h = int(view_w / target_aspect)
        view_x = (win_w - view_w) // 2
        view_y = (win_h - view_h) // 2
        glViewport(
            int(view_x * self.pixel_scale),
            int(view_y * self.pixel_scale),
            int(view_w * self.pixel_scale),
            int(view_h * self.pixel_scale),
        )
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, 1, 0, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_FASTEST)
        self.screen_size = np.array([view_w, view_h])
        self.screen_offset = np.array([view_x, view_y])
        self.load_shaders()
        try:
            f = pygame.font.SysFont("Arial", 100)
        except TypeError:
            f = pygame.font.Font(pygame.font.get_default_font(), 100)
        local_width = f.size(self.control_text)[0]
        if self.reference_width and local_width:
            self.text_scale = self.reference_width / local_width
        else:
            self.text_scale = 1.0
    def clear_images(self):
        glDeleteTextures(list(self.textures.values()))
        self.textures = {}
        self.rendered_text = {}
    def delete_image(self, name):
        glDeleteTextures([self.textures[name]])
        del self.textures[name]
    def load_image(self, name, image_path):
        surface = pygame.image.load(resource_path(image_path)).convert_alpha()
        width, height = surface.get_size()
        image_data = pygame.image.tostring(surface, "RGBA", True)
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        try:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        except GLError:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, image_data)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.textures[name] = texture_id
    def draw_image(self, name, position, size, alpha=None, direction=None):
        if alpha is not None:
            glColor4f(1.0, 1.0, 1.0, alpha)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        texture_id = self.textures[name]
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glBegin(GL_QUADS)
        if direction is None:
            glTexCoord2f(0, 0);
            glVertex2f(position[0] - size[0] / 2, position[1] - size[1] / 2)
            glTexCoord2f(1, 0);
            glVertex2f(position[0] + size[0] / 2, position[1] - size[1] / 2)
            glTexCoord2f(1, 1);
            glVertex2f(position[0] + size[0] / 2, position[1] + size[1] / 2)
            glTexCoord2f(0, 1);
            glVertex2f(position[0] - size[0] / 2, position[1] + size[1] / 2)
        else:
            position = np.asarray(position, dtype=float)
            aspect = self.screen_size[0] / self.screen_size[1]
            scale = np.array([aspect, 1.0])
            d = np.asarray(direction, dtype=float)
            d = d / np.linalg.norm(d)
            perp = np.array([-d[1], d[0]])
            w_vec = (size[0] * aspect / 2 * d) / scale
            h_vec = (size[1] / 2 * perp) / scale
            glTexCoord2f(0, 0);
            glVertex2f(*(position - w_vec - h_vec))
            glTexCoord2f(1, 0);
            glVertex2f(*(position + w_vec - h_vec))
            glTexCoord2f(1, 1);
            glVertex2f(*(position + w_vec + h_vec))
            glTexCoord2f(0, 1);
            glVertex2f(*(position - w_vec + h_vec))
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()
        glColor4f(1.0, 1.0, 1.0, 1.0)
    def clear_screen(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    def convert_mouse(self, mouse):
        mouse = (mouse - self.screen_offset) / self.screen_size
        mouse[1] = 1 - mouse[1]
        mouse = np.clip(mouse, 0, 1)
        return mouse
    def draw_lines(self, points, color, width, loop=False):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glColor4f(*color)
        width = width / 864 * self.screen_size[1]
        if width != 0:
            glLineWidth(width)
        if loop and width:
            glBegin(GL_LINE_LOOP)
        elif width == 0:
            glBegin(GL_POLYGON)
        else:
            glBegin(GL_LINE_STRIP)
        for point in points:
            glVertex2f(point[0], point[1])
        glEnd()
        glColor4f(1.0, 1.0, 1.0, 1.0)
    def draw_polygon(self, points, color):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glColor4f(*color)
        glBegin(GL_POLYGON)
        for point in points:
            glVertex2f(point[0], point[1])
        glEnd()
        glColor4f(1.0, 1.0, 1.0, 1.0)
    def draw_circle(self, position, radius, color, width=0):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glColor4f(*color)
        if width == 0:
            glBegin(GL_TRIANGLE_FAN)
            glVertex2f(position[0], position[1])
            for i in range(33):
                angle = 2 * 3.1415926 * i / 32
                dx = math.cos(angle) * radius
                dy = math.sin(angle) * radius * 16 / 9
                glVertex2f(position[0] + dx, position[1] + dy)
            glEnd()
        else:
            glLineWidth(width)
            glBegin(GL_LINE_LOOP)
            for i in range(32):
                angle = 2 * 3.1415926 * i / 32
                dx = math.cos(angle) * radius
                dy = math.sin(angle) * radius * 16 / 9
                glVertex2f(position[0] + dx, position[1] + dy)
            glEnd()
        glColor4f(1.0, 1.0, 1.0, 1.0)
    def load_pygame_surface(self, name, surface):
        surface = surface.convert_alpha()
        width, height = surface.get_size()
        image_data = pygame.image.tostring(surface, "RGBA", True)
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        try:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        except GLError:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, image_data)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.textures[name] = texture_id
    def generate_mipmaps(self, name):
        texture_id = self.textures[name]
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)
    def draw_map_section(self, name, cam):
        texture_id = self.textures[name]
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        u1 = max(0, (cam[0] - 960) / 5045)
        v1 = max(0, (cam[1] - 540) / 5045)
        u2 = min(1, (cam[0] + 960) / 5045)
        v2 = min(1, (cam[1] + 540) / 5045)
        glBegin(GL_QUADS)
        glTexCoord2f(u1, v2);
        glVertex2f(0, 0)
        glTexCoord2f(u2, v2);
        glVertex2f(1, 0)
        glTexCoord2f(u2, v1);
        glVertex2f(1, 1)
        glTexCoord2f(u1, v1);
        glVertex2f(0, 1)
        glEnd()
        glDisable(GL_TEXTURE_2D)
    def save_screen(self):
        pixels = glReadPixels(self.screen_offset[0], self.screen_offset[1], self.screen_size[0], self.screen_size[1],
                              GL_RGBA, GL_UNSIGNED_BYTE)
        surface = pygame.image.fromstring(pixels, self.screen_size, "RGBA")
        surface = pygame.transform.flip(surface, False, True)
        return surface
    def load_text(self, text, color, size, position, name, outline=0, outline_color=(0, 0, 0), fix=None, width_limit=1, font=None, direction=None):
        px_size = max(1, int(round(size * self.screen_size[1] / 864)))
        font = pygame.font.Font(resource_path("assets/ari-w9500.ttf"), px_size)
        base = font.render(text, True, color)
        text_size = base.get_size()
        if outline:
            thickness = outline
            width = text_size[0] + thickness * 2
            height = text_size[1] + thickness * 2
            text_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            outline_render = font.render(text, True, outline_color)
            if outline > 3:
                for angle in range(0, 360, 15):
                    dx = int(math.cos(math.radians(angle)) * thickness) + thickness
                    dy = int(math.sin(math.radians(angle)) * thickness) + thickness
                    text_surface.blit(outline_render, (dx, dy))
            else:
                for dx, dy in [(-thickness, 0), (thickness, 0), (0, -thickness), (0, thickness),
                               (-thickness, -thickness), (-thickness, thickness), (thickness, -thickness),
                               (thickness, thickness)]:
                    text_surface.blit(outline_render, (dx + thickness, dy + thickness))
            text_surface.blit(base, (thickness, thickness))
        else:
            text_surface = base
        crop = text_surface.get_bounding_rect(min_alpha=1)
        if crop.width and crop.height:
            text_surface = text_surface.subsurface(crop).copy()
        px_w, px_h = text_surface.get_size()
        self.load_pygame_surface(name, text_surface)
        norm_h = px_h / self.screen_size[1]
        norm_w = px_w * self.text_scale / self.screen_size[0]
        if norm_w > width_limit:
            norm_w = width_limit
        text_size = (norm_w, norm_h)
        if fix == 'left':
            position = (position[0] + text_size[0] / 2, position[1])
        elif fix == 'right':
            position = (position[0] - text_size[0] / 2, position[1])
        self.rendered_text[name] = [name, position, text_size, direction]
    def move_text(self, name, position, fix=None):
        if fix == 'left':
            position = (position[0] + self.rendered_text[name][2][0] / 2, position[1])
        elif fix == 'right':
            position = (position[0] - self.rendered_text[name][2][0] / 2, position[1])
        self.rendered_text[name][1] = position
    def draw_text(self, name, alpha=None):
        self.draw_image(self.rendered_text[name][0], self.rendered_text[name][1], self.rendered_text[name][2],
                        alpha=alpha, direction=self.rendered_text[name][3])
    def update_texture(self, texture, name):
        height, width = texture.shape[:2]
        flipped = np.flipud(texture)
        if name in self.textures:
            texture_id = self.textures[name]
        else:
            texture_id = glGenTextures(1)
            self.textures[name] = texture_id
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, flipped)
    def zoom(self, scale, center, offset):
        glTranslatef(center[0], center[1], 0.0)
        glScalef(scale, scale, 1.0)
        glTranslatef(-center[0], -center[1], 0.0)
        glTranslatef(-offset[0], -offset[1], 0.0)
    def load_shaders(self):
        def compile_one(src, shader_type):
            shader = glCreateShader(shader_type)
            glShaderSource(shader, src)
            glCompileShader(shader)
            if not glGetShaderiv(shader, GL_COMPILE_STATUS):
                raise RuntimeError(glGetShaderInfoLog(shader))
            return shader
        def compile_two(vs_src, fs_src):
            program = glCreateProgram()
            vs = compile_one(vs_src, GL_VERTEX_SHADER)
            fs = compile_one(fs_src, GL_FRAGMENT_SHADER)
            glAttachShader(program, vs)
            glAttachShader(program, fs)
            glLinkProgram(program)
            if not glGetProgramiv(program, GL_LINK_STATUS):
                raise RuntimeError(glGetProgramInfoLog(program))
            glDeleteShader(vs)
            glDeleteShader(fs)
            return program
        w, h = self.screen_size
        self.shader_buffer = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.shader_buffer)
        self.shader_buffer_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.shader_buffer_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.shader_buffer_texture, 0)
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("FBO incomplete")
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        vert_shader = """
        void main() {
            gl_TexCoord[0] = gl_MultiTexCoord0;
            gl_Position = ftransform();
        }
        """
        frag_shader = """
        uniform sampler2D screen;
        uniform vec2 texel;
        void main() {
            vec2 uv = gl_TexCoord[0].st;
            vec3 c = texture2D(screen, uv).rgb;
            float diff = 0.0;
            for (int x = -1; x <= 1; x++) {
                for (int y = -1; y <= 1; y++) {
                    if (x == 0 && y == 0) continue;
                    vec3 n = texture2D(screen, uv + vec2(x, y) * texel).rgb;
                    diff = max(diff, length(c - n));
                }
            }
            if (diff > 0.25)
                gl_FragColor = vec4(0, 0, 0, 1);
            else
                gl_FragColor = vec4(c, 1);
        }
        """
        invert_shader = """
        uniform sampler2D screen;
        void main() {
            vec3 c = texture2D(screen, gl_TexCoord[0].st).rgb;
            gl_FragColor = vec4(1.0 - c, 1);
        }
        """
        pixelation_shader = """
        uniform sampler2D screen;
        uniform vec2 texel; // size of one pixel in normalized UVs
        void main() {
            vec2 uv = gl_TexCoord[0].st;
            float px = 180.0; // number of square blocks along height
            float aspect = 16.0 / 9.0; // screen aspect ratio
            // scale UVs so blocks are square in screen space
            vec2 scaledUV = uv;
            scaledUV.x *= aspect;
            // floor to pixel grid
            scaledUV = floor(scaledUV * px) / px;
            // undo scaling
            scaledUV.x /= aspect;
            vec3 color = texture2D(screen, scaledUV).rgb;
            gl_FragColor = vec4(color, 1);
        }
        """
        rgb_shift_shader = """
        uniform sampler2D screen;
        uniform vec2 texel;
        void main() {
            vec2 uv = gl_TexCoord[0].st;
            float offset = 0.005;
            float r = texture2D(screen, uv + vec2(offset,0)).r;
            float g = texture2D(screen, uv).g;
            float b = texture2D(screen, uv - vec2(offset,0)).b;
            gl_FragColor = vec4(r, g, b, 1);
        }
        """
        vignette_shader = """
        uniform sampler2D screen;
        void main() {
            vec2 uv = gl_TexCoord[0].st;
            vec2 center = vec2(0.5, 0.5);
            float dist = distance(uv, center);
            float factor = smoothstep(0.8, 0.5, dist);
            vec3 color = texture2D(screen, uv).rgb * factor;
            gl_FragColor = vec4(color, 1);
        }
        """
        noise_shader = """
        uniform sampler2D screen;
        uniform float time;
        float rand(vec2 co){
            // scale co to a reasonable range
            return fract(sin(dot(co * 12.9898, vec2(78.233, 37.719))) * 43758.5453);
        }
        void main() {
            vec2 uv = gl_TexCoord[0].st;
            vec3 color = texture2D(screen, uv).rgb;
            float noise = rand(uv + vec2(time * 0.05 / 100000.0, time * 0.05 / 100000.0));
            // add small noise, clamp to [0,1]
            color += vec3(noise * 0.2);
            color = clamp(color, 0.0, 1.0);
            gl_FragColor = vec4(color, 1);
        }
        """
        wave_shader = """
        uniform sampler2D screen;
        uniform float time;
        void main() {
            vec2 uv = gl_TexCoord[0].st;
            uv.y += 0.03 * sin(uv.x * 30.0 + time / 1000.0);
            uv.x += 0.03 * cos(uv.y * 30.0 + time / 1000.0);
            vec3 color = texture2D(screen, uv).rgb;
            gl_FragColor = vec4(color, 1);
        }
        """
        self.shaders.append(compile_two(vert_shader, frag_shader))
        self.shaders.append(compile_two(vert_shader, wave_shader))
        self.shaders.append(compile_two(vert_shader, noise_shader))
        self.shaders.append(compile_two(vert_shader, vignette_shader))
        self.shaders.append(compile_two(vert_shader, rgb_shift_shader))
        self.shaders.append(compile_two(vert_shader, pixelation_shader))
        self.shaders.append(compile_two(vert_shader, invert_shader))
        _VERT = """
        varying vec2 lineUV;
        void main() {
            lineUV = gl_MultiTexCoord0.xy;
            gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
        }
        """
        _FRAG = """
        varying vec2 lineUV;
        uniform vec3 lineColor;
        float hash(vec2 p) {
            return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
        }
        float noise(vec2 p) {
            vec2 i = floor(p);
            vec2 f = fract(p);
            f = f * f * (3.0 - 2.0 * f);
            return mix(
                mix(hash(i),               hash(i + vec2(1, 0)), f.x),
                mix(hash(i + vec2(0, 1)),  hash(i + vec2(1, 1)), f.x),
                f.y
            );
        }
        void main() {
            float across = lineUV.y;  // -1 … +1 across the stroke
            // Rough, uneven edge using noise on the along-line coordinate
            float edgeNoise = (noise(vec2(lineUV.x * 60.0, 0.5)) - 0.5) * 0.18;
            float edgeDist  = abs(across) + edgeNoise;
            if (edgeDist > 1.0) discard;
            // Soft feathered falloff toward the edges
            float alpha = smoothstep(1.0, 0.55, edgeDist) * 0.88;
            // Worn ink texture variation
            float worn  = noise(vec2(lineUV.x * 30.0, across * 6.0)) * 0.14;
            vec3  color = lineColor * (0.82 + worn);
            // Faint center highlight — like ink slightly raised
            float centerGlow = (1.0 - abs(across) * 0.85) * 0.07;
            color += vec3(centerGlow);
            gl_FragColor = vec4(color, alpha);
        }
        """
        def _compile(src, kind):
            s = glCreateShader(kind)
            glShaderSource(s, src)
            glCompileShader(s)
            if not glGetShaderiv(s, GL_COMPILE_STATUS):
                raise RuntimeError(glGetShaderInfoLog(s).decode())
            return s
        prog = glCreateProgram()
        glAttachShader(prog, _compile(_VERT, GL_VERTEX_SHADER))
        glAttachShader(prog, _compile(_FRAG, GL_FRAGMENT_SHADER))
        glLinkProgram(prog)
        if not glGetProgramiv(prog, GL_LINK_STATUS):
            raise RuntimeError(glGetProgramInfoLog(prog).decode())
        self._line_shader = prog
        self._line_u_color = glGetUniformLocation(prog, "lineColor")
    def start_shader(self, n):
        self.shader_number = n
        w, h = self.screen_size
        glBindFramebuffer(GL_FRAMEBUFFER, self.shader_buffer)
        glViewport(0, 0, w, h)
        glClear(GL_COLOR_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    def end_shader(self):
        w, h = self.screen_size
        ox, oy = self.screen_offset
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(ox, oy, w, h)
        glClear(GL_COLOR_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, 1, 0, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glUseProgram(self.shaders[self.shader_number])
        t_loc = glGetUniformLocation(self.shaders[self.shader_number], "time")
        glUniform1f(t_loc, pygame.time.get_ticks())
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.shader_buffer_texture)
        glUniform1i(glGetUniformLocation(self.shaders[self.shader_number], "screen"), 0)
        glUniform2f(
            glGetUniformLocation(self.shaders[self.shader_number], "texel"),
            1.0 / w,
            1.0 / h
        )
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0);
        glVertex2f(0, 0)
        glTexCoord2f(1, 0);
        glVertex2f(1, 0)
        glTexCoord2f(1, 1);
        glVertex2f(1, 1)
        glTexCoord2f(0, 1);
        glVertex2f(0, 1)
        glEnd()
        glUseProgram(0)
opengl_manager = OpenglManager()
OVERLAY_ACTION = pygame.USEREVENT + 2
class OverlayManager:
    def __init__(self):
        self.steal_events = False
        self.ec_open = False
        self.ec_action = None
        self.ec_position = (0.5, 0.5)
        self.ec_size = (0.4, 0.3)
        self.ec_text_size = 48
        self.ec_pressed = False
        self.ec_mouse_relative_position = (0, 0)
        self.ec_button_size = (0.12, 0.08)
        self.ec_button_offset = (-0.1, -0.06)
    def event_check(self, events, overlay_events):
        if self.ec_open:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    get_pressed = pygame.mouse.get_pressed()
                    if get_pressed[0] or get_pressed[2]:
                        mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
                        if abs(mouse[0] - self.ec_position[0]) > self.ec_size[0] / 2 or abs(mouse[1] - self.ec_position[1]) > self.ec_size[1] / 2:
                            self.close_ec()
                            return
                        else:
                            button1 = (self.ec_position[0] + self.ec_button_offset[0], self.ec_position[1] + self.ec_button_offset[1])
                            button2 = (self.ec_position[0] - self.ec_button_offset[0], self.ec_position[1] + self.ec_button_offset[1])
                            if abs(mouse[0] - button1[0]) < self.ec_button_size[0] / 2 and abs(mouse[1] - button1[1]) < self.ec_button_size[1] / 2:
                                overlay_events.append(pygame.event.Event(OVERLAY_ACTION, action=self.ec_action))
                                self.close_ec()
                                return
                            elif abs(mouse[0] - button2[0]) < self.ec_button_size[0] / 2 and abs(mouse[1] - button2[1]) < self.ec_button_size[1] / 2:
                                self.close_ec()
                                return
                            else:
                                self.ec_pressed = True
                                self.ec_mouse_relative_position = (self.ec_position[0] - mouse[0], self.ec_position[1] - mouse[1])
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.ec_pressed = False
                elif event.type == pygame.MOUSEMOTION:
                    if self.ec_pressed:
                        mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
                        self.ec_position = (mouse[0] + self.ec_mouse_relative_position[0], mouse[1] + self.ec_mouse_relative_position[1])
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.close_ec()
                        return
                    elif event.key == pygame.K_RETURN:
                        overlay_events.append(pygame.event.Event(OVERLAY_ACTION, action=self.ec_action))
                        self.close_ec()
                        return
        return
    def render(self):
        if self.ec_open:
            cx, cy = self.ec_position
            w, h = self.ec_size
            left = cx - w / 2
            right = cx + w / 2
            top = cy + h / 2
            bottom = cy - h / 2
            button1 = (self.ec_position[0] + self.ec_button_offset[0], self.ec_position[1] + self.ec_button_offset[1])
            button2 = (self.ec_position[0] - self.ec_button_offset[0], self.ec_position[1] + self.ec_button_offset[1])
            button_width, button_height = self.ec_button_size
            bg_color = (1, 1, 1, 0.7)
            border_color = (0, 0, 0, 1.0)
            button_color = (0, 0, 0, 1.0)
            opengl_manager.draw_lines([(right, top), (left, top), (left, bottom), (right, bottom)], bg_color, 0, True)
            opengl_manager.draw_lines([(right, top), (left, top), (left, bottom), (right, bottom)], border_color, 10, True)
            if 'ec_title' in opengl_manager.textures:
                opengl_manager.move_text('ec_title', (self.ec_position[0], self.ec_position[1] + 0.09))
                opengl_manager.draw_text('ec_title')
            else:
                self.close_ec()
                return
            opengl_manager.draw_lines([(button1[0] + button_width/2, button1[1] - button_height/2), (button1[0] + button_width/2, button1[1] + button_height/2), (button1[0] - button_width/2, button1[1] + button_height/2), (button1[0] - button_width/2, button1[1] - button_height/2)], button_color, 0, True)
            opengl_manager.draw_lines([(button2[0] + button_width/2, button2[1] - button_height/2), (button2[0] + button_width/2, button2[1] + button_height/2), (button2[0] - button_width/2, button2[1] + button_height/2), (button2[0] - button_width/2, button2[1] - button_height/2)], button_color, 0, True)
            if 'ec_yes' in opengl_manager.textures:
                opengl_manager.move_text('ec_yes', button1)
                opengl_manager.draw_text('ec_yes')
            else:
                self.close_ec()
                return
            if 'ec_no' in opengl_manager.textures:
                opengl_manager.move_text('ec_no', button2)
                opengl_manager.draw_text('ec_no')
            else:
                self.close_ec()
                return
    def open_ec(self, text, action=None):
        self.ec_open = True
        self.steal_events = True
        self.ec_action = action
        opengl_manager.load_text(f'Do you want to {text}?', (0, 0, 0), self.ec_text_size, (0, 0), 'ec_title', width_limit=self.ec_size[0] * 0.9, outline=1)
        opengl_manager.load_text('Yes', (255, 255, 255), self.ec_text_size, (0, 0), 'ec_yes')
        opengl_manager.load_text('No', (255, 255, 255), self.ec_text_size, (0, 0), 'ec_no')
    def close_ec(self):
        self.ec_open = False
        self.steal_events = False
overlay_manager = OverlayManager()
class Player:
    def __init__(self, position, scene):
        self.position = np.array(position)
        self.new_position = None
        self.direction = np.array((1, 0))
        self.speed = 5
        self.selected_suggestions = np.array([])
        self.move_animation = 0
        self.scene = scene
        self.frame = 0
    def update_speed(self, speed):
        self.speed = speed
    def set_direction(self, direction):
        self.direction = np.array(direction)
    def generate_suggestions(self, direction):
        return self.position + direction[None, :] * np.arange(1, self.speed + 1)[:, None]
    def move_possible(self, direction=None):
        if direction is None:
            direction = self.direction
        suggestions = self.generate_suggestions(direction).astype(int)
        xs = suggestions[:, 0]
        ys = suggestions[:, 1]
        rows, cols = self.scene.level.shape
        on_board = (xs >= 0) & (xs < cols) & (ys >= 0) & (ys < rows)
        if not np.all(on_board):
            return 0
        if np.any(self.scene.level[ys, xs] == 1):
            return 0
        return 1
    def update_move_suggestion(self, mouse=None):
        if mouse is not None:
            screen_position = self.scene.grid_to_screen(self.position + np.array([0.5, 0.5]))
            offset = mouse - screen_position
            if abs(offset[0]) > abs(offset[1]):
                if offset[0] > 0:
                    self.direction = (1, 0)
                else:
                    self.direction = (-1, 0)
            else:
                if offset[1] > 0:
                    self.direction = (0, 1)
                else:
                    self.direction = (0, -1)
            self.direction = np.array(self.direction)
        rows, cols = self.scene.level.shape
        def filter_valid(suggestions):
            if len(suggestions) == 0:
                return suggestions
            valid = []
            for cell in suggestions:
                x, y = int(cell[0]), int(cell[1])
                if not (0 <= x < cols and 0 <= y < rows):
                    break
                if self.scene.level[y, x] == 1:
                    break
                valid.append(cell)
            if not valid:
                return np.empty((0, 2), dtype=suggestions.dtype)
            return np.array(valid, dtype=suggestions.dtype)
        self.selected_suggestions = filter_valid(self.generate_suggestions(self.direction))
    def render_move_suggestion(self):
        if len(self.selected_suggestions) == 0:
            return
        move_possible = self.move_possible()
        direction_names = {
            (1, 0): 'right',
            (-1, 0): 'left',
            (0, -1): 'down',
            (0, 1): 'up',
        }
        sprite_name = ('green_' if move_possible else 'red_') + direction_names[tuple(self.direction)]
        last_index = len(self.selected_suggestions) - 1
        for i, cell in enumerate(self.selected_suggestions):
            animation = math.sin(((cell[0] + cell[1]) * 5 + self.frame) % 30 / 30 * math.pi) * 0.1
            position = self.scene.grid_to_screen(cell + np.array([0.5, 0.5 + animation]))
            if i == last_index:
                icon = 'tick' if move_possible else 'cross'
                opengl_manager.draw_image(icon, position, (self.scene.cell_w, self.scene.cell_h))
            else:
                opengl_manager.draw_image(sprite_name, position, (self.scene.cell_w, self.scene.cell_h))
        return
    def update(self, countdown_tiles=None):
        if self.new_position is not None:
            self.move_animation += 0.04
            if self.move_animation >= 0.95:
                if countdown_tiles is not None:
                    for tile in countdown_tiles:
                        if np.linalg.norm(self.new_position - self.position) == np.linalg.norm(tile.grid_position - self.position) + np.linalg.norm(tile.grid_position - self.new_position):
                            if self.new_position[0] != tile.grid_position[0] or self.new_position[1] != tile.grid_position[1]:
                                tile.tick()
                self.position = self.new_position
                self.new_position = None
                self.move_animation = 0
                self.update_move_suggestion()
        self.frame += 1
    def move(self, direction=None):
        if self.new_position is not None:
            return 0
        if direction is None:
            direction = self.direction
        else:
            self.direction = direction
        if self.move_possible(direction=direction):
            self.new_position = self.position + self.speed * self.direction
            self.update_move_suggestion()
            self.move_animation = 0
            return 1
        else:
            return 0
    def render(self):
        if self.new_position is None:
            px, py = self.position
        else:
            move_progress = 3 * self.move_animation ** 2 - 2 * self.move_animation ** 3
            px, py = self.new_position * move_progress + self.position * (1 - move_progress)
        opengl_manager.draw_image('player_shadow', self.scene.grid_to_screen((px + 0.5, py + 0.5)), (self.scene.cell_w * 4/3, self.scene.cell_h * 4/3))
        if self.direction[0] == 0:
            if self.direction[1] > 0:
                costume = f"mouse{int(self.frame / 5) % 6 + 13}"
            else:
                costume = f"mouse{int(self.frame / 5) % 6 + 7}"
        else:
            if self.direction[0] > 0:
                costume = f"mouse{int(self.frame / 5) % 6 + 1}"
            else:
                costume = f"mouse{int(self.frame / 5) % 6 + 19}"
        opengl_manager.draw_image(costume, self.scene.grid_to_screen((px + 0.5, py + 0.5)), (self.scene.cell_w * 4/3, self.scene.cell_h * 4/3))
levels_completed = 0
def get_levels_completed():
    return levels_completed
def set_levels_completed(value):
    global levels_completed
    levels_completed = value
class SceneManager:
    def __init__(self):
        self.scene_name = None
    def first_scene(self):
        scene = HomeScene()
        self.scene_name = 'home'
        return scene
    def update_scene(self, scene):
        if scene.change_scene:
            if scene.change_scene == 'game':
                scene = GameScene(scene.next_level)
                self.scene_name = 'game'
            elif scene.change_scene == 'home':
                scene = HomeScene()
                self.scene_name = 'home'
        return scene
scene_manager = SceneManager()
pygame.mixer.init()
class SoundManager:
    def __init__(self):
        self.music_volume = 0.5
        self.sfx_volume = 0.2
        self.sound_effects = {
            'move': pygame.mixer.Sound(resource_path('assets/move.wav')),
            'windup': pygame.mixer.Sound(resource_path('assets/windup.wav')),
            'ticking': pygame.mixer.Sound(resource_path('assets/ticking.wav')),
            'cdt_tick': pygame.mixer.Sound(resource_path('assets/countdown-tile-tick.wav')),
            'cdt_activate': pygame.mixer.Sound(resource_path('assets/countdown-tile-activate.wav')),
            'victory': pygame.mixer.Sound(resource_path('assets/victory.wav')),
            'defeat': pygame.mixer.Sound(resource_path('assets/defeat.wav')),
        }
        for sound in self.sound_effects.values():
            sound.set_volume(self.sfx_volume)
        self.channel = pygame.mixer.find_channel()
        self.music_tracks = {
            'menu': 'assets/soundtrack_menu.mp3',
            'game': 'assets/soundtrack.mp3',
        }
        self.current_track = None
        self.duck_effects = ('victory', 'defeat')
        self.music_duck_factor = 1
        self.music_restore_step = 0.01
        self.duck_channel = None
        self.music_ducked = False
    def set_volume(self, value):
        value = max(0.0, min(1.0, value))
        self.music_volume = value
        self.sfx_volume = value * 0.4
        pygame.mixer.music.set_volume(self.music_volume)
        for sound in self.sound_effects.values():
            sound.set_volume(self.sfx_volume)
    def start_music(self):
        self.play_music('menu')
    def play_music(self, track):
        if track == self.current_track:
            return
        self.current_track = track
        pygame.mixer.music.load(resource_path(self.music_tracks[track]))
        pygame.mixer.music.set_volume(self.music_volume)
        pygame.mixer.music.play(-1)
    def play_move(self):
        self.channel.play(self.sound_effects['move'])
    def play_effect(self, name):
        channel = self.sound_effects[name].play()
        if name in self.duck_effects:
            self.duck_channel = channel
            self.music_ducked = True
            pygame.mixer.music.set_volume(self.music_volume * self.music_duck_factor)
        return channel
    def update_music(self):
        if not self.music_ducked:
            return
        if self.duck_channel is not None and self.duck_channel.get_busy():
            return
        volume = min(self.music_volume, pygame.mixer.music.get_volume() + self.music_restore_step)
        pygame.mixer.music.set_volume(volume)
        if volume >= self.music_volume:
            self.music_ducked = False
            self.duck_channel = None
    def update_ticking(self, active):
        playing = self.channel.get_sound() if self.channel.get_busy() else None
        if not active:
            if playing is self.sound_effects['ticking']:
                self.channel.stop()
            return
        if playing is self.sound_effects['move']:
            return
        if playing is not self.sound_effects['ticking']:
            self.channel.play(self.sound_effects['ticking'], loops=-1)
sound_manager = SoundManager()
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
pygame.init()
opengl_manager.create_screen()
pygame.display.set_caption("Wind Up")
FPS = 60
def main():
    clock = pygame.time.Clock()
    running = True
    scene = scene_manager.first_scene()
    sound_manager.start_music()
    while running:
        events = pygame.event.get()
        if overlay_manager.steal_events:
            overlay_events = []
            overlay_manager.event_check(events, overlay_events)
            events = overlay_events
        running = scene.event_check(events)
        if not running:
            break
        scene.update()
        scene.render()
        overlay_manager.render()
        sound_manager.update_music()
        scene = scene_manager.update_scene(scene)
        pygame.display.flip()
        clock.tick_busy_loop(FPS)
    print('window closed')
    pygame.quit()
if __name__ == '__main__':
    main()
