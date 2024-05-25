import os
import threading
from queue import Queue
from Utils import trace_exception
from typing import List, Callable

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame import mixer


class MusicHandler(threading.Thread):
    AUDIO_FORMATS = (".mp3", ".ogg", ".wav")

    def __init__(self,
                 name="MediaHandler",
                 music_dir="",
                 editors: List[str] = None,
                 callback: Callable[[str], None] = lambda x: None):

        threading.Thread.__init__(self)
        self.name = name
        self.folder = music_dir
        self.editors = editors
        self.__reply = callback

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

    def __add_song(self, filename: str):
        self.__song_queue.put(filename)

    def __skip_song(self):
        if self.__song_queue.empty():
            mixer.music.stop()
        else:
            self.__load_from_queue()

    @staticmethod
    def _get_songs(folder: str):
        return [*filter(
            lambda x: os.path.splitext(x)[1] in MusicHandler.AUDIO_FORMATS,
            os.listdir(folder)
        )]

    @staticmethod
    def _search_song(name: str, folder: str):
        songs = MusicHandler._get_songs(folder)

        if name.isdigit():
            i = int(name)
            if len(songs) >= i > 0:
                return songs[i - 1]

        for filename in songs:
            if name.lower() in os.path.splitext(filename)[0].lower():
                return filename
        return ""

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

            if self.running and not self.__msg_queue.empty():
                user, command = self.__msg_queue.get()
                self.__msg_queue.task_done()

                try:
                    if command.startswith("!sr ") and len(command) > 4:
                        song = self._search_song(command[4:], self.folder)
                        if song:
                            self.__add_song(os.path.join(self.folder, song))
                            self.__reply(f"{os.path.splitext(song)[0]} has been added to the queue.")
                            if not self.playing:
                                self.__load_from_queue()
                        else:
                            self.__reply("A matching song was not found.")

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
                            self.__reply(f"Volume now set to {new_vol * 100}")

                        else:
                            match command:
                                case "!play":   mixer.music.unpause()
                                case "!pause":  mixer.music.pause()
                                case "!skip":   self.__skip_song()
                                case "!rewind": mixer.music.rewind()
                                case "!songs": self.__reply(
                                    ", ".join(f"{i}. {os.path.splitext(name)[0]}"
                                              for i, name in enumerate(self._get_songs(self.folder), 1)))
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
