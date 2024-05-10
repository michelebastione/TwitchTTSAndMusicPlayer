import os
import json
import random
import threading
from queue import Queue

import typing
from typing import List

import pyttsx3
from pyttsx3.voice import Voice


class TTSHandler(threading.Thread):
    def __init__(self, config: dict, name='TTSHandler'):
        threading.Thread.__init__(self)
        self.name = name
        self.banned_from_tts = config["banned"]
        self.users_settings = config["users_settings"]

        self.__engine: pyttsx3.Engine
        self.__message_queue: Queue[tuple[str, str]] = Queue()
        self._voices: List[Voice] = []
        self._users = self._load_users()
        self.running = False

    def _load_users(self):
        filename = self.users_settings
        if os.path.exists(filename):
            with open(filename) as file:
                return json.load(file)
        else:
            return {}

    def _save_users(self):
        filename = self.users_settings
        with open(filename, 'w') as f:
            json.dump(self._users, f)

    def add_message(self, username, message):
        self.__message_queue.put((username, message))

    def __change_voice(self, username, message):
        tokens = message.split()
        if tokens[0] != '!voice':
            return False

        voice_name = tokens[1].upper()
        user_voice = self._users[username][0]

        for index, voice in enumerate(self._voices):
            id_name = str(voice.id).rsplit('\\', 1)[1].strip('1234567890._').upper()

            # handle 2-letter codes separately, so that we don't just match the first name that contains those letters
            if len(voice_name) == 2 and f'{voice_name}-' in id_name or f'{voice_name}_' in id_name:
                user_voice = index
                break
            elif voice_name in id_name:
                user_voice = index
                break

        try:
            rate = int(tokens[-1])
        except ValueError:
            rate = self._users[username][1]

        self._users[username] = (user_voice, rate)
        return True

    def run(self):
        print('TTS Handler Starting!')
        self.__engine = pyttsx3.init()
        self.__engine.startLoop(False)
        self._voices = typing.cast(List[Voice], self.__engine.getProperty('voices'))

        self.running = True
        while self.running:
            if self.__message_queue.empty():
                self.__engine.iterate()
                continue

            username, message = self.__message_queue.get()
            self.__message_queue.task_done()

            if username in self.banned_from_tts:
                continue
            if username not in self._users:
                self._users[username] = (random.randrange(len(self._voices)), random.randint(180, 220))

            if message.startswith('!voice '):
                if self.__change_voice(username, message):
                    self.__engine.setProperty('voice', self._voices[self._users[username][0]].id)
                    self.__engine.setProperty('rate', self._users[username][1])
                    self.__engine.say(f'{username} has changed voices')
            else:
                try:
                    self.__engine.setProperty('voice', self._voices[self._users[username][0]].id)
                except IndexError:
                    self.__engine.setProperty('voice', self._voices[0].id)
                self.__engine.setProperty('rate', self._users[username][1])
                self.__engine.say(message)

        self.__engine.endLoop()

    def stop(self):
        print('TTS handler stopping')
        self._save_users()
        self.running = False
