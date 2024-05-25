import re
import threading
import asyncio as aio
from queue import Queue
from emoji import demojize
from Utils import trace_exception
from TTSHandler import TTSHandler
from MusicHandler import MusicHandler


class TwitchReader(threading.Thread):
    TTS_COMMANDS = {"!voice "}
    MUSIC_COMMANDS = {"!sr ", "!play", "!pause", "!skip", "!rewind", "!vol ", "!songs"}
    MSG_PATTERN = re.compile(r':(.*)!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*?) :(.*)')
    LINK_PATTERN = re.compile(r'http(s?)://\S+|\S+\.com/\S+')

    def __init__(self, config: dict, name='TwitchReader', tts=False, music=False):
        threading.Thread.__init__(self)
        self.name = name
        self._config = config

        self.__stream_reader: aio.StreamReader
        self.__stream_writer: aio.StreamWriter

        self._tts_handler: TTSHandler | None = None
        self._music_handler: MusicHandler | None = None
        self.add_plugins(tts, music)

        self.__replies_queue: Queue[str] = Queue()

        self.debug_output = False
        self.running = False

    def add_plugins(self, tts=False, music=False):
        if tts:
            self._tts_handler = TTSHandler(self._config["tts"], callback=self.callback_handler)
            self._tts_handler.start()
        if music:
            music_dir = self._config["music"]["directory"]
            editors = self._config["music"]["editors"] + [self._config["twitch"]["nickname"]]
            self._music_handler = MusicHandler(music_dir=music_dir, editors=editors, callback=self.callback_handler)
            self._music_handler.start()

    async def plugins_ready(self):
        while ((not self._tts_handler.running if self._tts_handler else False)
                or (not self._music_handler.running if self._music_handler else False)):
            await aio.sleep(0.05)

    @staticmethod
    def parse_msg(message):
        message = demojize(message).replace('\r', '')
        username, channel, message = re.search(TwitchReader.MSG_PATTERN, message).groups()
        # remove web links
        message = re.sub(TwitchReader.LINK_PATTERN, 'web link', message)
        return username, message

    async def __read(self):
        msg = await self.__stream_reader.read(2048)
        return msg.decode('utf-8')

    async def __write(self, message: str):
        self.__stream_writer.write(message.encode("utf-8"))
        await self.__stream_writer.drain()

    def callback_handler(self, cb_arg: str):
        self.__replies_queue.put(cb_arg)

    async def __handle_incoming_messages(self):
        while self.running:
            try:
                raw_msg = await self.__read()
                if raw_msg.startswith('PING'):
                    await self.__write("PONG :tmi.twitch.tv2 3\n")
                elif 'PRIVMSG' in raw_msg:
                    user, msg = self.parse_msg(raw_msg)
                    if self._music_handler is not None and any(msg.startswith(cmd) for cmd in self.MUSIC_COMMANDS):
                        self._music_handler.add_message(user, msg)
                    elif self._tts_handler is not None:
                        self._tts_handler.add_message(user, msg)

                    if self.debug_output:
                        print(raw_msg)

            except Exception as e:
                trace_exception(e)

    async def __handle_outgoing_replies(self):
        channel = self._config["twitch"]["channel"]
        while self.running:
            if self.__replies_queue.empty():
                await aio.sleep(0.05)
                continue

            try:
                reply = self.__replies_queue.get()
                self.__replies_queue.task_done()
                await self.__write(f'PRIVMSG {channel} :{reply}\n')

            except Exception as e:
                trace_exception(e)

    async def __handle_client(self):
        print('Connecting to Twitch...')
        settings = self._config["twitch"]
        self.__stream_reader, self.__stream_writer = await aio.open_connection(settings["server"], settings["port"])

        try:
            await self.__write(f'PASS {settings["token"]}\n')
            await self.__write(f'NICK {settings["nickname"]}\n')
            await self.__write(f'JOIN {settings["channel"]}\n')
            print('Connection established - Entering Chat loop')

            await self.plugins_ready()
            self.running = True

            incoming_task = self.__handle_incoming_messages()
            outgoing_task = self.__handle_outgoing_replies()
            await aio.gather(incoming_task, outgoing_task)

        except aio.CancelledError:
            print("A task was cancelled during handling of chat messages")
        except Exception as e:
            trace_exception(e)
        finally:
            self.__stream_writer.close()

    def run(self):
        aio.run(self.__handle_client())

    def stop(self):
        self.running = False

        if self._tts_handler:
            self._tts_handler.stop()
            self._tts_handler.join()
        if self._music_handler:
            self._music_handler.stop()
            self._music_handler.join()

        print("Disconnecting from Twitch...")
        self.__stream_writer.close()
