# Twitch TTS and Music Player

This is a custom text to speech program using the **pyttsx3** library and the ability to play chat song requests directly on the host using **pygame**'s **mixer** library.

Gives new users a random voice selected from the ones installed, and allows them to change their voice using the `!voice` command. 
Add a song request to the queue by typing `!sr` followed by the song name or part of it, or even its index in the list.
Available audio formats are `.mp3` `.wav` and `.ogg`.

## Installation

1. Install the latest version of [Python](https://www.python.org/downloads/).
2. Download the [contents of this repository](https://github.com/michelebastione/TwitchTTSAndMusicPlayer/archive/refs/heads/main.zip) and unzip them into a folder.
3. Open the command line and run the following command:
	`pip install -r requirements.txt`
4. Open `appsettings.json` with your text editor of choice and do the following:
	- Generate an OAuth token for your channel using [this tool](https://twitchapps.com/tmi/) and replace `twitch\TOKEN_HERE` with the generated token.
	- Replace `twitch\nickname` and `twitch\#channelname` with the name of your channel (keeping the `#` in the latter).
	- At the voice `music\directory`, add the local path to your music folder.
	- At the voice `music\editors`, Add the nicknames of the users you want to make able to skip songs, change volume, etc...
5. (Optional) Ban specific users from using tts adding them to `tts\banned`
6. The TTS and Music Player is now ready to be used, and can be ran by double clicking `Main.py`.

## Installing Alternate Voices

In order for the TTS to use alternate voices, the language packs must be installed on your machine.

[How to install language packs for Windows](https://support.microsoft.com/en-us/windows/language-packs-for-windows-a5094319-a92d-18de-5b53-1cfc697cfca8)

[How to install language packs for Mac](https://www.imore.com/how-add-new-languages-your-mac) (Untested. If you are able to get this working on mac, let me know!)

The TTS will only use speakers listed below, so installing additional language packs will have no effect.

## Using Alternate Voices

Alternate voices can be used by a user, but the voice package must first be installed on your machine See (Installing Alternate Voices) before running `Main.py`.

A user can switch voices by using typing the command `!voice [Speaker] [Rate]`.

The `[Speaker]` value can be either a `code` or a `name` from the table below.

|Language|Code|Name|
|---|---|---|
|English (US) (Male)|US|David|
|English (US) (Female)|US|Zira|
|English (GB)|GB|Hazel|
|German|DE|Hedda|
|Spanish (Spain)|ES|Helena|
|Spanish (Mexico)|MX|Sabina|
|French|FR|Hortense|
|Italian|IT|Elsa|
|Japanese|JP|Haruka|
|Korean|KR|Heami|
|Polish|PL|Paulina|
|Portrugese|BR|Maria|
|Russian|RU|Irina|
|Chinese (China)|CN|Huihui|
|Chinese (Hong Kong)|HK|Tracy|
|Chinese (Taiwan)|TW|Hanhan|

In cases where the `code` is the same for different speakers, the speaker name must be specified instead.

The `rate` is a number (the default is 200).


## Music Player commands
Users in chat can add songs to the playlist by typing `!sr` followed by the song name, part of it, or even its index. 
If a match is found in the specified music directory of the host computer the song will be added to the reproduction queue.

Users specified as editors can also use the following commands:
- `!pause`: Pause the reproduction
- `!play`: Unpause the reproduction
- `!skip`: Skip the current song
- `!rewind`: Replay the current song before it ends
- `!vol up`: Increase volume by 10%
- `!vol down`: Decrease volume by 10%
- `!vol [value]`: Sets the volume to the specified value (1-100)
- `!songs`: Show list of all possible songs to request
