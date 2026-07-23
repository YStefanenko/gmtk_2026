import pygame
from overlay_manager import overlay_manager, OVERLAY_ACTION
from opengl_manager import opengl_manager
import numpy as np
from levels import levels
from player import Player


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

        self.player = Player((0, 0), self)

        self.level = np.array(levels['0'][::-1])
        self.change_scene = None

        self.cell_w = self.cell_h = self.offset_x = self.offset_y = 0
        self.calculate_grid()

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
                if self.player.new_position is None:
                    self.player.update_move_suggestion(mouse)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.player.move()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    overlay_manager.open_ec("close the game")

                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.player.move()

                elif event.key in (pygame.K_w, pygame.K_UP):
                    self.player.move(np.array((0, 1)))
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    self.player.move(np.array((0, -1)))
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    self.player.move(np.array((-1, 0)))
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.player.move(np.array((1, 0)))

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
        if self.player.new_position is None:
            self.player.render_move_suggestion()

        self.player.render()
