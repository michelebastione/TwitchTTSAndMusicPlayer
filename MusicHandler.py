import os
import json
import threading
from queue import Queue
from Utils import trace_exception
from typing import List, Callable

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame import mixer


class MusicHandler(threading.Thread):
    def __init__(self,
                 name="MediaHandler",
                 music_dir="",
                 editors: List[str] = None,
                 callback: Callable[[str], None] = lambda x: None):

        threading.Thread.__init__(self)
        self.name = name
        self.folder = music_dir
        self.editors = editors
        self.__callback = callback

        self.__msg_queue: Queue[tuple[str, str]] = Queue()
        self.__song_queue: Queue[str] = Queue()
        self.__audio_end_event = pygame.NOEVENT

        self.running = False
        self.playing = False

    def __init_music_player(self):
        pygame.init()
        mixer.init()
        self.__audio_end_event = pygame.event.custom_type()
        mixer.music.set_endevent(self.__audio_end_event)

    def add_message(self, username, message):
        self.__msg_queue.put((username, message))

    def __load_from_queue(self):
        if not self.__song_queue.empty():
            song = self.__song_queue.get()
            self.__song_queue.task_done()

            try:
                mixer.music.load(song)
                mixer.music.play()
                self.playing = True
            except Exception as e:
                trace_exception(e)

    def __add_song(self, filename):
        self.__song_queue.put(filename)

    def __skip_song(self):
        if self.__song_queue.empty():
            mixer.music.stop()
        else:
            self.__load_from_queue()

    @staticmethod
    def __search_song(name, folder):
        for filename in os.listdir(folder):
            if name.lower() in os.path.splitext(filename)[0].lower():
                return filename
        else:
            return ""

    @staticmethod
    def __load_config():
        with open("music_config.json") as m_config:
            conf = json.load(m_config)
            m_dir, editors = conf["directory"], conf["editors"]

        with open("appsettings.json") as t_config:
            conf = json.load(t_config)
            editors.append(conf["nickname"])

        return m_dir, editors

    def run(self):
        print("Music handler is starting...")
        self.running = True
        self.__init_music_player()
        print("Music handler has been started correctly")

        while self.running:
            for event in pygame.event.get():
                match event.type:
                    case self.__audio_end_event:
                        # at the end of a song we start playing the next one from the queue
                        self.playing = False
                        self.__load_from_queue()
                    case pygame.QUIT:
                        # we have to use pygame.quit() inside the event loop in order to stop it gracefully
                        self.running = False
                        pygame.quit()
                        break
                    case _:
                        pass

            if not self.running:
                break
            if self.__msg_queue.empty():
                continue

            user, command = self.__msg_queue.get()
            self.__msg_queue.task_done()

            try:
                if command.startswith("!sr "):
                    song = self.__search_song(command[4:], self.folder)
                    if song:
                        self.__add_song(os.path.join(self.folder, song))
                        self.__callback(f"{os.path.splitext(song)[0]} has been added to the queue.")
                        if not self.playing:
                            self.__load_from_queue()
                    else:
                        print("A matching song was not found.")

                elif user in self.editors:
                    if command.startswith("!vol ") and len(command) > 5:
                        curr_vol = mixer.music.get_volume()
                        new_vol = curr_vol
                        match command.split()[1]:
                            case "up":   new_vol = curr_vol + 0.1
                            case "down": new_vol = curr_vol - 0.1
                            case _ as value:
                                if value.isdigit():
                                    new_vol = int(value) / 100
                        mixer.music.set_volume(new_vol)
                        self.__callback(f"Volume now set to {new_vol * 100}")

                    else:
                        match command:
                            case "!play":   mixer.music.unpause()
                            case "!pause":  mixer.music.pause()
                            case "!skip":   self.__skip_song()
                            case "!rewind": mixer.music.rewind()
                            case _: pass

            except Exception as e:
                trace_exception(e)

    def stop(self):
        if self.running:
            print("Music handler is stopping...")
            mixer.music.unload()
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        else:
            print("The music handler is not running")
