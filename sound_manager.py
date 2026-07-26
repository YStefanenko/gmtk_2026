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
            'cdt_tick': pygame.mixer.Sound(resource_path('assets/countdown-tile-tick.wav')),
            'cdt_activate': pygame.mixer.Sound(resource_path('assets/countdown-tile-activate.wav')),
            'victory': pygame.mixer.Sound(resource_path('assets/victory.wav')),
            'defeat': pygame.mixer.Sound(resource_path('assets/defeat.wav')),
        }
        for sound in self.sound_effects.values():
            sound.set_volume(self.sfx_volume)

        self.channel = pygame.mixer.find_channel()

        self.duck_effects = ('victory', 'defeat')
        self.music_duck_factor = 0.1
        self.music_restore_step = 0.01
        self.duck_channel = None
        self.music_ducked = False

    def start_music(self):
        pygame.mixer.music.load(resource_path('assets/sound_track.mp3'))
        pygame.mixer.music.set_volume(self.music_volume)
        pygame.mixer.music.play(-1)

    def play_move(self):
        self.channel.play(self.sound_effects['move'])

    def play_effect(self, name):
        channel = self.sound_effects[name].play()
        if name in self.duck_effects:
            self.duck_channel = channel
            self.music_ducked = True
            pygame.mixer.music.set_volume(self.music_volume * self.music_duck_factor)
        return channel

    def update_music(self):
        if not self.music_ducked:
            return
        if self.duck_channel is not None and self.duck_channel.get_busy():
            return
        volume = min(self.music_volume, pygame.mixer.music.get_volume() + self.music_restore_step)
        pygame.mixer.music.set_volume(volume)
        if volume >= self.music_volume:
            self.music_ducked = False
            self.duck_channel = None

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
