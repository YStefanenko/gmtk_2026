from game_scene import GameScene
from home_scene import HomeScene


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
