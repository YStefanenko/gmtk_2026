from opengl_manager import opengl_manager
import numpy as np
import pygame
import math


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

        # Any cell off the board blocks the move.
        if not np.all(on_board):
            return 0

        # Any cell over a wall (value 1) blocks the move.
        if np.any(self.scene.level[ys, xs] == 1):  # level is indexed [y][x]
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
                    break  # off board — stop, don't just skip this one cell
                if self.scene.level[y, x] == 1:
                    break  # wall — everything further out is unreachable too
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

    def update(self):
        if self.new_position is not None:
            self.move_animation += 0.04
            if self.move_animation >= 0.95:
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

        # bx, by = self.scene.grid_to_screen((px + 0.1, py + 0.1))
        # tx, ty = self.scene.grid_to_screen((px + 0.9, py + 0.9))
        #
        # points = [(bx, by), (tx, by), (tx, ty), (bx, ty)]
        #
        # opengl_manager.draw_polygon(points, (0, 0, 1, 1))
        # opengl_manager.draw_lines(points, (0, 0, 0, 1), width=3, loop=True)
        # if self.new_position is None:
        #     costume = f"mouse{int(self.frame/3) % 6 + 1}"
        # else:
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