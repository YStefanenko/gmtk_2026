OUTPUT_FILE = 'app.py'

# 📝 List the files you want to include below
FILES_TO_INCLUDE = [
    'game_scene.py',
    'home_scene.py',
    'levels.py',
    'opengl_manager.py',
    'overlay_manager.py',
    'player.py',
    'scene_manager.py',
    'sound_manager.py',
    'timer.py',
]

def extract_top_level_code(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    class_started = False
    top_level_lines = []
    class_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('class '):
            class_started = True
        if class_started:
            class_lines.append(line)
        elif stripped and not stripped.startswith(('import', 'from', '#')):
            # Top-level assignments or constants
            top_level_lines.append(line)

    return ''.join(top_level_lines), ''.join(class_lines)

def collect_classes_and_globals():
    all_blocks = ['''
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
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
import math
''']

    for file_path in FILES_TO_INCLUDE:
        try:
            globals_code, class_code = extract_top_level_code(file_path)
            combined = f"# From {file_path}\n"
            if globals_code.strip():
                combined += globals_code + '\n'
            if class_code.strip():
                combined += class_code
            all_blocks.append(combined)
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
    all_blocks.append('''    
pygame.init()

opengl_manager.create_screen()

pygame.display.set_caption("Your moves are running out")

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

        scene = scene_manager.update_scene(scene)

        pygame.display.flip()

        clock.tick_busy_loop(FPS)

    print('window closed')
    pygame.quit()


if __name__ == '__main__':
    main()
        ''')
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        out.write('\n\n'.join(all_blocks))

    print(f"✅ Combined {len(all_blocks)} files into {OUTPUT_FILE}")

def remove_comments_and_blank_lines(input_file, output_file=None):
    output_file = output_file or input_file  # overwrite by default

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    cleaned = []
    for line in lines:
        stripped = line.lstrip()  # only remove leading spaces for comment check
        if not stripped.strip():  # skip blank lines (even with spaces)
            continue
        if stripped.startswith('#'):  # skip full-line comments
            continue
        # Remove inline comment but preserve indentation
        code = line.split('#', 1)[0].rstrip()
        if code.strip():  # make sure there's actual code
            cleaned.append(code + '\n')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(cleaned)


collect_classes_and_globals()
remove_comments_and_blank_lines('app.py')
