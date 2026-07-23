from opengl_manager import opengl_manager
import numpy as np
import pygame


class Player:
    def __init__(self, position, scene):
        self.position = np.array(position)
        self.new_position = None
        self.direction = np.array((1, 0))
        self.speed = 5
        self.move_suggestions = np.array([])
        self.move_animation = 0
        self.scene = scene
        self.frame = 0

    def update_speed(self, speed):
        self.speed = speed

    def set_direction(self, direction):
        self.direction = np.array(direction)

    def generate_suggestions(self, direction):
        return self.position + direction[None, :] * np.arange(0, self.speed + 1)[:, None]

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

        suggestions = self.generate_suggestions(self.direction)

        # Keep only the cells that lie on the board.
        rows, cols = self.scene.level.shape
        xs, ys = suggestions[:, 0], suggestions[:, 1]
        on_board = (xs >= 0) & (xs < cols) & (ys >= 0) & (ys < rows)
        self.move_suggestions = suggestions[on_board]

    def render_move_suggestion(self):
        for cell in self.move_suggestions:
            bx, by = self.scene.grid_to_screen(cell + np.array([0.1, 0.1]))
            tx, ty = self.scene.grid_to_screen(cell + np.array([0.9, 0.9]))

            points = [(bx, by), (tx, by), (tx, ty), (bx, ty)]

            if self.move_possible():
                color = (0, 1, 0, 0.3)
            else:
                color = (1, 0, 0, 0.3)

            opengl_manager.draw_polygon(points, color)

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
        if direction is None:
            direction = self.direction

        if self.move_possible(direction=direction):
            self.direction = direction
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