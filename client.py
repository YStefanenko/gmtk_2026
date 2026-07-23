import os
import sys

os.chdir(os.path.dirname(sys.argv[0]))

# Force SDL to use primary monitor
if sys.platform == "darwin":
    os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
else:
    os.environ["SDL_VIDEO_WINDOW_POS"] = "100,100"

os.environ["SDL_VIDEO_CENTERED"] = "0"
os.environ["SDL_VIDEO_ALLOW_SCREENSAVER"] = "1"

# Disable DPI weirdness
os.environ["SDL_VIDEO_HIGHDPI_DISABLED"] = "1"

import pygame
from scene_manager import scene_manager
from opengl_manager import opengl_manager
from overlay_manager import overlay_manager

pygame.init()

opengl_manager.create_screen()

pygame.display.set_caption("Your moves are running out")

FPS = 60

# for i in range(24):
#     print(f"{[0 for j in range(24)]},")


def main():
    clock = pygame.time.Clock()
    running = True

    scene = scene_manager.first_scene()
    # sound_manager.start_music()

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

        scene = scene_manager.update_scene(scene)

        pygame.display.flip()

        clock.tick_busy_loop(FPS)

    print('window closed')
    pygame.quit()


if __name__ == '__main__':
    main()
