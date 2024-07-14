import os
import json
import random
import threading
from queue import Queue
from Utils import trace_exception

import typing
from typing import List, Callable, Dict
import pyttsx3
from pyttsx3.voice import Voice


class TTSHandler(threading.Thread):
    def __init__(self,
                 config: dict,
                 name='TTSHandler',
                 callback: Callable[[str], None] = lambda x: None):

        threading.Thread.__init__(self)
        self.name = name
        self.banned_from_tts = config["banned"]
        self.min_rate, self.max_rate = config["min_max_rate"]
        self.users_settings = config["users_settings"]
        self.__reply = callback

        self.__engine: pyttsx3.Engine | None = None
        self.__message_queue: Queue[tuple[str, str]] = Queue()
        self._voices: List[Voice] = []
        self._users: Dict[str, tuple[int, int]] = self._load_users()
        self.running = False

    def _load_users(self):
        filename = self.users_settings
        if os.path.exists(filename):
            with open(filename) as file:
                text = file.read()
                return json.loads(text) if text != "" else {}

    def _save_users(self):
        filename = self.users_settings
        with open(filename, 'w') as f:
            json.dump(self._users, f)

    def add_message(self, username: str, message: str):
        self.__message_queue.put((username, message))

    def __change_voice(self, username: str, message: str):
        tokens = message.split()
        name = tokens[1].upper()

        current_voice, current_rate = self._users[username]
        if len(tokens) > 2 and tokens[2].isdigit():
            rate = int(tokens[2])
            current_rate = (
                self.min_rate if rate < self.min_rate
                else self.max_rate if rate > self.max_rate
                else rate
            )

        for index, voice in enumerate(self._voices):
            voice_id = str(voice.id).rsplit('\\', 1)[-1].upper()

            # handle 2-letter codes separately, so that we don't just match the first name that contains those letters
            if (len(name) == 2 and f'{name}-' in voice_id or f'{name}_' in voice_id) or name in voice_id:
                current_voice = index
                break

        self._users[username] = (current_voice, current_rate)

    def __speak(self, username: str, message: str):
        voice, rate = self._users[username]
        self.__engine.setProperty('voice', self._voices[voice].id)
        self.__engine.setProperty('rate', rate)

        if message:
            self.__engine.say(message)

    def run(self):
        print('TTS Handler is starting...')
        self.__engine = pyttsx3.init()
        self.__engine.startLoop(False)
        self._voices = typing.cast(List[Voice], self.__engine.getProperty('voices'))
        print("TTS handler has been started correctly")

        try:
            self.running = True
            while self.running:
                if self.__message_queue.empty():
                    self.__engine.iterate()
                    continue

                username, message = self.__message_queue.get()
                self.__message_queue.task_done()

                if username not in self.banned_from_tts:
                    if username not in self._users or self._users[username][0] >= len(self._voices):
                        self._users[username] = (random.randrange(len(self._voices)), random.randint(180, 220))

                    if message.startswith('!voice '):
                        self.__change_voice(username, message)
                        self.__speak(username, f'{username} has changed voices')
                    else:
                        self.__speak(username, message)

            self.__engine.endLoop()

        except Exception as e:
            trace_exception(e)

    def stop(self):
        print('TTS handler is stopping...')
        self._save_users()
        self.running = False
