import os
import json
import threading
import pygame
from pygame import mixer

with open("music_config.json") as file:
    config = json.load(file)
    MUSIC_DIR, EDITORS = config["directory"], config["editors"]


class MusicHandler(threading.Thread):
    def __init__(self, name="MediaHandler"):
        threading.Thread.__init__(self)
        self.name = name
        self.msg_queue = []
        self.song_queue = []
        self.playlist_condition = threading.Condition()
        self.msg_condition = threading.Condition()
        self.audio_end_event = pygame.NOEVENT
        self.running = False
        self.is_playing = False

    def __init_music_player(self):
        pygame.init()
        mixer.init()
        self.audio_end_event = pygame.event.custom_type()
        mixer.music.set_endevent(self.audio_end_event)
        self.player_was_init = True

    def __load_from_queue(self):
        self.playlist_condition.acquire()
        if self.song_queue:
            try:
                song = self.song_queue.pop(0)
                mixer.music.load(song)
                mixer.music.play()
                self.is_playing = True
            except Exception as e:
                print(f"ERROR: {e.args[0]}")
        self.playlist_condition.notify()
        self.playlist_condition.release()

    def __add_to_queue(self, filename):
        path = os.path.join(MUSIC_DIR, filename)
        self.playlist_condition.acquire()
        self.song_queue.append(path)
        self.playlist_condition.notify()
        self.playlist_condition.release()

    def __skip_song(self):
        mixer.music.stop()
        self.__load_from_queue()

    @staticmethod
    def __search_song(name):
        for filename in os.listdir(MUSIC_DIR):
            if name.lower() in os.path.splitext(filename)[0].lower():
                return filename
        else:
            return ""

    def receive(self, username, message):
        self.msg_condition.acquire()
        self.msg_queue.append((username, message))
        self.msg_condition.notify()
        self.msg_condition.release()

    def stop(self):
        self.msg_condition.acquire()
        mixer.music.stop()
        mixer.music.unload()
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.msg_condition.notify()
        self.msg_condition.release()

    def run(self):
        print("Media handler starting!")
        self.running = True
        self.__init_music_player()

        while self.running:
            for event in pygame.event.get():
                match event.type:
                    case self.audio_end_event:
                        # at the end of a song we start playing the next one from the queue
                        self.playlist_condition.acquire()
                        self.is_playing = False
                        self.__load_from_queue()
                        self.playlist_condition.notify()
                        self.playlist_condition.release()
                    case pygame.QUIT:
                        self.running = False
                        # the quit method has to be inside the event loop so that we can exit it gracefully
                        pygame.quit()
                        break
                    case _:
                        pass

            if not self.running:
                break
            if not self.msg_queue:
                continue

            self.msg_condition.acquire()
            for user, command in self.msg_queue:
                try:
                    if command.startswith("!sr "):
                        song = self.__search_song(command[4:])
                        if song:
                            self.__add_to_queue(os.path.join(MUSIC_DIR, song))
                            print(f"{os.path.splitext(song)[0]} added to queue.")
                            if not self.is_playing:
                                self.__load_from_queue()
                        else:
                            print("A matching song was not found.")

                    elif user in EDITORS:
                        if command.startswith("!vol ") and len(command) > 5:
                            curr_vol = mixer.music.get_volume()
                            match command.split()[1]:
                                case "up":   mixer.music.set_volume(curr_vol + 0.1)
                                case "down": mixer.music.set_volume(curr_vol - 0.1)
                                case _ as value:
                                    if value.isdigit():
                                        mixer.music.set_volume(int(value) / 100)
                        else:
                            match command:
                                case "!play":   mixer.music.unpause()
                                case "!pause":  mixer.music.pause()
                                case "!skip":   self.__skip_song()
                                case "!rewind": mixer.music.rewind()
                                case _: pass

                except Exception as e:
                    print(e.args[0])

            self.msg_queue.clear()
            self.msg_condition.release()

        print("Media handler stopping")


if __name__ == "__main__":
    pygame.init()
    mixer.init()
    audio_end_evt = pygame.event.custom_type()
    mixer.music.set_endevent(audio_end_evt)
    mixer.music.load(os.path.join(MUSIC_DIR, "test.wav"))
    mixer.music.play()

    check = True
    while check:
        for evt in pygame.event.get():
            if evt.type == audio_end_evt:
                print("end")
                pygame.quit()
                check = False
                break
                