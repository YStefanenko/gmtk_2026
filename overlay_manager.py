import pygame
from opengl_manager import opengl_manager

OVERLAY_ACTION = pygame.USEREVENT + 2

class OverlayManager:
    def __init__(self):
        self.steal_events = False

        # Exit Confirmation
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

            bg_color = (0.08, 0.09, 0.11, 0.98)
            border_color = (0.3, 0.35, 0.4, 1.0)
            button_color = (0.12, 0.14, 0.18, 1.0)

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

        opengl_manager.load_text(f'Do you want to {text}?', (255, 255, 255), self.ec_text_size, (0, 0), 'ec_title', width_limit=self.ec_size[0] * 0.9)
        opengl_manager.load_text('Yes', (255, 255, 255), self.ec_text_size, (0, 0), 'ec_yes')
        opengl_manager.load_text('No', (255, 255, 255), self.ec_text_size, (0, 0), 'ec_no')


    def close_ec(self):
        self.ec_open = False
        self.steal_events = False


overlay_manager = OverlayManager()
