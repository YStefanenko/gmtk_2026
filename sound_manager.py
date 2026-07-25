import pygame
from resource import resource_path

pygame.mixer.init()


class SoundManager:
    def __init__(self):
        self.music_volume = 0.5
        self.sfx_volume = 0.2

        self.sound_effects = {
            'move': pygame.mixer.Sound(resource_path('assets/move.wav')),
            'windup': pygame.mixer.Sound(resource_path('assets/windup.wav')),
            'ticking': pygame.mixer.Sound(resource_path('assets/ticking.wav')),
        }
        for sound in self.sound_effects.values():
            sound.set_volume(self.sfx_volume)

        self.channel = pygame.mixer.find_channel()

    def start_music(self):
        pygame.mixer.music.load(resource_path('assets/sound_track.mp3'))
        pygame.mixer.music.set_volume(self.music_volume)
        pygame.mixer.music.play(-1)

    def play_move(self):
        self.channel.play(self.sound_effects['move'])

    def play_windup(self):
        self.sound_effects['windup'].play()

    def update_ticking(self, active):
        playing = self.channel.get_sound() if self.channel.get_busy() else None

        if not active:
            if playing is self.sound_effects['ticking']:
                self.channel.stop()
            return

        if playing is self.sound_effects['move']:
            return

        if playing is not self.sound_effects['ticking']:
            self.channel.play(self.sound_effects['ticking'], loops=-1)


sound_manager = SoundManager()
