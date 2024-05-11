import json
import typing
from typing import List
import pygame
from pygame import mixer
import pyttsx3
from pyttsx3.voice import Voice

from TTSHandler import TTSHandler
from TwitchReader import TwitchReader


def tts_test():
    engine = pyttsx3.init()
    voices = typing.cast(List[Voice], engine.getProperty('voices'))
    for i, v in enumerate(voices):
        print(v.id, f'\t[{i}]')
        engine.setProperty('voice', v.id)
        engine.say('this is a test message')
    engine.runAndWait()


def music_test():
    pygame.init()
    mixer.init()
    audio_end_evt = pygame.event.custom_type()
    mixer.music.set_endevent(audio_end_evt)
    mixer.music.load("test.wav")
    mixer.music.play()

    check = True
    while check:
        for evt in pygame.event.get():
            if evt.type == audio_end_evt:
                print("end")
                pygame.quit()
                check = False
                break


if __name__ == '__main__':
    tts_test()
    music_test()

    with open("appsettings.json") as config_file:
        config = json.load(config_file)

    reader = TwitchReader(config, tts=TTSHandler())
    reader.debug_output = True
    reader.run()
