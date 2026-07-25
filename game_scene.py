import pygame
from overlay_manager import overlay_manager, OVERLAY_ACTION
from opengl_manager import opengl_manager
import numpy as np
from levels import levels
from player import Player
from timer import Timer
from sound_manager import sound_manager

END_BTN_COLOR = (0.40, 0.30, 0.45, 1)
END_BTN_HOVER_COLOR = (0.60, 0.45, 0.65, 1)
END_BTN_OUTLINE = (0.85, 0.80, 0.85, 1)


class GameScene:
    def __init__(self, level):
        opengl_manager.clear_images()

        for asset in ['tick', 'cross', 'finish_tile', 'outerwall0', 'outerwall1', 'outerwall3', 'outerwall4', 'player_shadow', 'green_up', 'green_down', 'green_left', 'green_right', 'red_up', 'red_down', 'red_left', 'red_right']:
            image = pygame.image.load(f"assets/{asset}.png")
            image = pygame.transform.scale(image, (96, 96))
            opengl_manager.load_pygame_surface(asset, image)

        for name in ['tbar', 'ybar', 'bbar']:
            for i in range(1, 7):
                image = pygame.image.load(f"assets/{name}{i}.png")
                image = pygame.transform.scale(image, (96, 96))
                opengl_manager.load_pygame_surface(f"{name}{i}", image)

        for i in range(0, 11):
            image = pygame.image.load(f"assets/clock{i}.png")
            image = pygame.transform.scale(image, (96, 96))
            opengl_manager.load_pygame_surface(f"clock{i}", image)

        for i in range(0, 11):
            image = pygame.image.load(f"assets/clock{i}p.png")
            image = pygame.transform.scale(image, (96, 96))
            opengl_manager.load_pygame_surface(f"clock{i}p", image)

        for i in range(0, 10):
            image = pygame.image.load(f"assets/lfloor{i}.png")
            image = pygame.transform.scale(image, (96, 96))
            opengl_manager.load_pygame_surface(f"lfloor{i}", image)

        for i in range(0, 10):
            image = pygame.image.load(f"assets/dfloor{i}.png")
            image = pygame.transform.scale(image, (96, 96))
            opengl_manager.load_pygame_surface(f"dfloor{i}", image)

        for i in range(0, 22):
            if i == 17 or i == 20:
                continue
            image = pygame.image.load(f"assets/wall{i}.png")
            image = pygame.transform.scale(image, (96, 96))
            opengl_manager.load_pygame_surface(f"wall{i}", image)

        for i in range(0, 4):
            image = pygame.image.load(f"assets/top{i}.png")
            image = pygame.transform.scale(image, (96, 96))
            opengl_manager.load_pygame_surface(f"top{i}", image)

        for i in range(1, 25):
            image = pygame.image.load(f"assets/mouse{i}.png")
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

        self.player = Player(self.start, self)

        self.selected_timer = 0

        # Stack timers in a vertical column just to the right of the grid.
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
        self.end_button_hw = 0.16
        self.end_button_hh = 0.06
        self.hover_button = None



    def calculate_grid(self):
        rows, cols = self.level.shape

        rows += 5
        cols += 2

        # A physically square cell is (9/16, 1) in this 1x1 / 16:9 space.
        # Fill 90% of the limiting screen dimension; the other stays smaller.
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
                                self.change_scene = 'game'
                            elif action == 'retry':
                                self.next_level = self.current_level
                                self.change_scene = 'game'
                            break

            elif event.type == pygame.MOUSEMOTION:
                mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
                over_grid = (self.offset_x <= mouse[0] <= 1 - self.offset_x and self.offset_y <= mouse[1] <= 1 - self.offset_y)
                if over_grid and self.player.new_position is None:
                    self.player.update_move_suggestion(mouse)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
                for i in range(len(self.timers)):
                    if self.timers[i].is_pressed(mouse):
                        self.selected_timer = i
                        self.player.speed = self.timers[i].value
                        self.player.update_move_suggestion()
                        break
                else:
                    self.do_move()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    overlay_manager.open_ec("return to menu")

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
                    self.end_level(0)

        return 1

    def update(self):
        self.player.update()

        sound_manager.update_ticking(self.game)

    def render(self):
        opengl_manager.clear_screen()

        opengl_manager.draw_polygon([(0, 0), (1, 0), (1, 1), (0, 1)], (0.271, 0.157, 0.235, 1))

        # Render grid
        rows, cols = self.level.shape

        # Floor tiles
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

        opengl_manager.draw_image('finish_tile', self.grid_to_screen(self.finish + np.array([0.5, 0.5])), (self.cell_w, -self.cell_h))

        # Render outer stuff
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

        # Render player
        self.player.render_move_suggestion()
        self.player.render()

        # More outer stuff
        opengl_manager.draw_image('outerwall0', self.grid_to_screen((-0.5, -0.5)), (self.cell_w, self.cell_h))
        opengl_manager.draw_image('outerwall0', self.grid_to_screen((cols + 0.5, -0.5)), (self.cell_w, self.cell_h))
        opengl_manager.draw_image('outerwall1', self.grid_to_screen((-0.5, 0.5)), (self.cell_w, self.cell_h))
        opengl_manager.draw_image('outerwall1', self.grid_to_screen((cols + 0.5, 0.5)), (self.cell_w, self.cell_h))
        for r in range(1, rows+1):
            opengl_manager.draw_image('wall11', self.grid_to_screen((-0.5, r + 0.5)), (self.cell_w, self.cell_h))
            opengl_manager.draw_image('wall11', self.grid_to_screen((cols + 0.5, r + 0.5)), (self.cell_w, self.cell_h))
        opengl_manager.draw_image('outerwall3', self.grid_to_screen((-0.5, rows + 1.5)), (self.cell_w, self.cell_h))
        opengl_manager.draw_image('outerwall4', self.grid_to_screen((cols + 0.5, rows + 1.5)), (self.cell_w, self.cell_h))

        # Draw walls
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

        # Wall tops
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

        # Render timers
        for i in range(len(self.timers)):
            self.timers[i].render(print_as_selected=(i == self.selected_timer))

        if not self.game:
            opengl_manager.draw_text('end1')
            for action, cx, cy, name in self.end_buttons:
                fill = END_BTN_HOVER_COLOR if self.hover_button == action else END_BTN_COLOR
                corners = [(cx - self.end_button_hw, cy - self.end_button_hh),
                           (cx + self.end_button_hw, cy - self.end_button_hh),
                           (cx + self.end_button_hw, cy + self.end_button_hh),
                           (cx - self.end_button_hw, cy + self.end_button_hh)]
                opengl_manager.draw_polygon(corners, fill)
                opengl_manager.draw_lines(corners, END_BTN_OUTLINE, 2, loop=True)
                opengl_manager.draw_text(name)


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
        sound_manager.play_windup()

        cy = 0.34
        left_cx = 0.5 - 0.18
        right_cx = 0.5 + 0.18

        if result:
            opengl_manager.load_text('Level Complete', (128, 128, 128), 128, (0.5, 0.5), 'end1', 10)
            right_action, right_label = 'next', 'Next Level'
        else:
            opengl_manager.load_text('Level Failed', (128, 128, 128), 128, (0.5, 0.5), 'end1', 10)
            right_action, right_label = 'retry', 'Try Again'

        opengl_manager.load_text('Back to Menu', (240, 235, 245), 40, (left_cx, cy), 'end_btn_left')
        opengl_manager.load_text(right_label, (240, 235, 245), 40, (right_cx, cy), 'end_btn_right')

        self.end_buttons = [
            ('menu', left_cx, cy, 'end_btn_left'),
            (right_action, right_cx, cy, 'end_btn_right'),
        ]


    def do_move(self, direction=None):
        if self.player.speed <= 0:
            return

        moved = self.player.move(direction)
        self.player.update_move_suggestion()
        if moved:
            self.timers[self.selected_timer].tick()
            self.player.speed = self.timers[self.selected_timer].value
            sound_manager.play_move()
