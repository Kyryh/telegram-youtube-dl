# Telegram Youtube downloader

telegram-youtube-dl is a telegram bot made in Python that helps you download videos from YouTube, Reddit, Tiktok and many other websites.

It mainly uses the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) and [yt-dlp](https://github.com/yt-dlp/yt-dlp) libraries, alongside some other smaller ones.

## Usage

This bot isn't available to the public at the moment, so you'll have to host it yourself.

## Hosting

- Install python 3.9+

- Clone the repository
  ```bash
  git clone https://github.com/Kyryh/telegram-youtube-dl.git
  cd telegram-youtube-dl
  ```
- Optionally:
  - Create a virtual environment
    ```bash
    python -m venv .venv
    ```
  - Activate the virtual environment
    
    Windows:
    ```bash
    .venv\Scripts\activate
    ```
    Unix/MacOS:
    ```bash
    source .venv/bin/activate
    ```
- Install the requirements
  ```bash
  python -m pip install -r requirements.txt
  ```
- Install FFMPEG in your system (you can probably figure it out on your own)
- Create a `.env` file with the contents of `.env.template` (simply copy-paste then rename)
- Fill out the values in the `.env` file
- Finally, run the telegram bot
  ```bash
  python __main__.py
  ```
- To update the bot to the latest version, do a simple `git pull`

## Issues and other stuff
Feel free to open an issue if you have any doubts and/or you found something that doesn't work

Also feel free to contribute by opening a pull request, the bot is far from perfect and I would appreciate some help
