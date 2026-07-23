import pygame
from overlay_manager import overlay_manager, OVERLAY_ACTION
from opengl_manager import opengl_manager
import numpy as np
from levels import levels
from player import Player
from timer import Timer


class GameScene:
    def __init__(self):
        opengl_manager.clear_images()
        opengl_manager.load_image('tile1', 'assets/tile1.png')
        opengl_manager.load_image('tile2', 'assets/tile2.png')
        opengl_manager.load_image('wall1', 'assets/wall1.png')

        for i in range(1, 25):
            image = pygame.image.load(f"assets/mouse{i}.png")
            image = pygame.transform.scale(image, (128, 128))
            opengl_manager.load_pygame_surface(f"mouse{i}", image)

        self.level = np.array(levels['0'][::-1])

        self.cell_w = self.cell_h = self.offset_x = self.offset_y = 0
        self.calculate_grid()

        self.player = Player((0, 0), self)

        self.selected_timer = 0

        # Stack timers in a vertical column just to the right of the grid.
        timer_values = [5, 4, 3]
        timer_size = 0.15
        timer_radius_x = timer_size / 2 * 9 / 16
        grid_right = 1 - self.offset_x
        column_x = grid_right + timer_radius_x + 0.01  # almost touching the grid
        spacing = timer_size + 0.05
        top_y = 0.85
        self.timers = [Timer(value, i,(column_x, top_y - i * spacing), size=timer_size) for i, value in enumerate(timer_values)]

        self.player.speed = self.timers[self.selected_timer].value

        self.change_scene = None



    def calculate_grid(self):
        rows, cols = self.level.shape

        # A physically square cell is (9/16, 1) in this 1x1 / 16:9 space.
        # Fill 90% of the limiting screen dimension; the other stays smaller.
        self.cell_h = min(0.9 / rows, 0.9 * 16 / 9 / cols)
        self.cell_w = self.cell_h * 9 / 16
        self.offset_x = (1 - cols * self.cell_w) / 2
        self.offset_y = (1 - rows * self.cell_h) / 2

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
        for event in events:
            if event.type == pygame.QUIT:
                return 0

            elif event.type == OVERLAY_ACTION:
                return 0

            elif event.type == pygame.MOUSEMOTION:
                mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
                over_grid = (self.offset_x <= mouse[0] <= 1 - self.offset_x and
                             self.offset_y <= mouse[1] <= 1 - self.offset_y)
                if over_grid and self.player.new_position is None:
                    self.player.update_move_suggestion(mouse)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse = opengl_manager.convert_mouse(pygame.mouse.get_pos())
                for timer in self.timers:
                    if timer.is_pressed(mouse):
                        self.selected_timer = timer.index
                        self.player.speed = timer.value
                        self.player.update_move_suggestion()
                        break
                else:
                    if self.player.speed > 0:
                        moved = self.player.move()
                        if moved:
                            self.timers[self.selected_timer].tick()
                            self.player.speed = self.timers[self.selected_timer].value

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    overlay_manager.open_ec("close the game")

                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self.player.speed > 0:
                        moved = self.player.move()
                        if moved:
                            self.timers[self.selected_timer].tick()
                            self.player.speed = self.timers[self.selected_timer].value

                elif event.key in (pygame.K_w, pygame.K_UP):
                    if self.player.speed > 0:
                        moved = self.player.move(np.array((0, 1)))
                        if moved:
                            self.timers[self.selected_timer].tick()
                            self.player.speed = self.timers[self.selected_timer].value

                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    if self.player.speed > 0:
                        moved = self.player.move(np.array((0, -1)))
                        if moved:
                            self.timers[self.selected_timer].tick()
                            self.player.speed = self.timers[self.selected_timer].value

                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    if self.player.speed > 0:
                        moved = self.player.move(np.array((-1, 0)))
                        if moved:
                            self.timers[self.selected_timer].tick()
                            self.player.speed = self.timers[self.selected_timer].value

                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    if self.player.speed > 0:
                        moved = self.player.move(np.array((1, 0)))
                        if moved:
                            self.timers[self.selected_timer].tick()
                            self.player.speed = self.timers[self.selected_timer].value


        return 1

    def update(self):
        self.player.update()

    def render(self):
        opengl_manager.clear_screen()

        # Render grid
        rows, cols = self.level.shape

        for r in range(rows):
            for c in range(cols):
                position = self.grid_to_screen((c + 0.5, r + 0.5))

                if self.level[r][c] == 1:
                    costume = f"wall1"
                else:
                    costume = f"tile{(r+c)%2 + 1}"
                opengl_manager.draw_image(costume, position, (self.cell_w, self.cell_h))

        # Render player
        self.player.render_move_suggestion()

        self.player.render()

        # Render timers
        for timer in self.timers:
            timer.render(print_as_selected=(timer.index == self.selected_timer))
