from game_scene import GameScene


class SceneManager:
    def __init__(self):
        self.scene_name = None

    def first_scene(self):
        scene = GameScene(0)
        self.scene_name = 'home'
        return scene

    def update_scene(self, scene):
        if scene.change_scene:
            if scene.change_scene == 'game':
                scene = GameScene(scene.next_level)
                self.scene_name = 'game'

        return scene


scene_manager = SceneManager()
