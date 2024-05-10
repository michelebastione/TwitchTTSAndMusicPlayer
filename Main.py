import json
import time

from TwitchReader import TwitchReader
from TTSHandler import TTSHandler
from MusicHandler import MusicHandler


if __name__ == '__main__':
    with open("appsettings.json") as config_file:
        config = json.load(config_file)

    tts_config = config["tts"]
    tts = TTSHandler(tts_config)

    music_dir = config["music"]["directory"]
    editors = config["music"]["editors"] + [config["twitch"]["nickname"]]
    music = MusicHandler(music_dir=music_dir, editors=editors)

    twitch_config = config["twitch"]
    reader = TwitchReader(twitch_config, tts_handler=tts, music_handler=music)

    tts.start()
    music.start()
    reader.start()

    # wait for twitch reader to start
    while not reader.running:
        time.sleep(0.05)

    input('Main: ENTER ANYTHING TO HALT\r\n')

    tts.stop()
    music.stop()
    reader.stop()

    tts.join()
    music.join()
    reader.join()
    print('Main: closing')
