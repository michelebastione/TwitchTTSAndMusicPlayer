from TwitchReader import TwitchReader
from TTSHandler import TTSHandler
from MusicHandler import MusicHandler

if __name__ == '__main__':
    reader = TwitchReader()
    tts_handler = TTSHandler()
    media_handler = MusicHandler()
    reader.tts_handler = tts_handler
    reader.media_handler = media_handler

    tts_handler.start()
    media_handler.start()
    reader.start()

    input('Main: ENTER ANYTHING TO HALT\r\n')
    print('Main: closing')
    tts_handler.save_users()

    tts_handler.stop()
    media_handler.stop()
    reader.stop()

    tts_handler.join()
    media_handler.join()
    reader.join()
