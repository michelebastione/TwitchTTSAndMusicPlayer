import json
import time
from Utils import trace_exception
from TwitchReader import TwitchReader


if __name__ == '__main__':
    try:
        print("The application is initializing...\n")

        with open("appsettings.json") as config_file:
            config = json.load(config_file)

        reader = TwitchReader(config, tts=True, music=True)
        reader.start()

        # wait for twitch reader to start
        while not reader.running:
            time.sleep(0.05)

        input('\nENTER ANYTHING TO HALT\n')

        reader.stop()
        reader.join()
        print('The application is shutting down')

    except Exception as e:
        trace_exception(e, "Fatal error")
