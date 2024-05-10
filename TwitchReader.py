import re
import threading
import asyncio as aio
from emoji import demojize

from TTSHandler import TTSHandler
from MusicHandler import MusicHandler


class TwitchReader(threading.Thread):
    TTS_COMMANDS = {"!voice "}
    MUSIC_COMMANDS = {"!sr ", "!play", "!pause", "!skip", "!rewind", "!vol "}
    MSG_PATTERN = re.compile(r':(.*)!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*?) :(.*)')
    LINK_PATTERN = re.compile(r'http(s?)://\S+|\S+\.com/\S+')

    def __init__(self, config: dict, name='TwitchReader', tts_handler=None, music_handler=None):
        threading.Thread.__init__(self)
        self.name = name
        self._config = config

        self.stream_reader: aio.StreamReader
        self.stream_writer: aio.StreamWriter

        self.tts_handler: TTSHandler = tts_handler
        self.music_handler: MusicHandler = music_handler
        self.debug_output = False
        self.running = False

    @staticmethod
    def parse_msg(message):
        message = demojize(message).replace('\r', '')
        username, channel, message = re.search(TwitchReader.MSG_PATTERN, message).groups()
        # remove web links
        message = re.sub(TwitchReader.LINK_PATTERN, 'web link', message)
        return username, message

    async def __read(self):
        msg = await self.stream_reader.read(2048)
        return msg.decode('utf8')

    async def __write(self, message):
        self.stream_writer.write(message.encode("utf-8"))
        await self.stream_writer.drain()

    async def __handle_client(self):
        print('Connecting to Twitch')
        self.stream_reader, self.stream_writer = await aio.open_connection(self._config["server"], self._config["port"])

        try:
            await self.__write(f'PASS {self._config["token"]}\n')
            await self.__write(f'NICK {self._config["nickname"]}\n')
            await self.__write(f'JOIN {self._config["channel"]}\n')
            print('Connection established - Entering Chat loop')

            self.running = True
            while self.running:
                try:
                    resp = await self.__read()
                    if resp.startswith('PING'):
                        await self.__write("PONG :tmi.twitch.tv2 3\n")
                    elif 'PRIVMSG' in resp:
                        user, msg = self.parse_msg(resp)
                        if any(msg.startswith(cmd) for cmd in self.MUSIC_COMMANDS) and self.music_handler is not None:
                            self.music_handler.receive(user, msg)
                        elif self.tts_handler is not None:
                            self.tts_handler.add_message(user, msg)
                            # await self._write(f'PRIVMSG {self._config["channel"]} :received message\n')

                        if self.debug_output:
                            print(resp)

                except aio.CancelledError as e:
                    print(e.args[0])
                    break

        except Exception as e:
            print(e.args[0])
        finally:
            self.stream_writer.close()

    def run(self):
        aio.run(self.__handle_client())

    def stop(self):
        self.running = False
        self.stream_writer.close()
