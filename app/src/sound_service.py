import pygame

class SoundService:
    def __init__(self):
        pygame.init()
        self.sound = pygame.mixer.Sound("success.mp3")

    def play(self):
        self.sound.play()

if __name__ == "__main__":
    sound_service = SoundService()
    sound_service.play()

    # Keep the script running until the sound is played
    while pygame.mixer.get_busy():
        pygame.time.Clock().tick(10)