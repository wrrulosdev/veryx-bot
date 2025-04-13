import subprocess
import sys
import os

import discord
from discord.ext.commands.bot import Bot
from loguru import logger
from dotenv import load_dotenv
from ezjsonpy import load_language, set_language, translate_message

from .bot import DiscordBot
from .constants import BotConstants, FilePath

load_dotenv()


class Main:
    def __init__(self) -> None:
        subprocess.run('clear || cls', shell=True)
        
        if not os.path.exists(FilePath.EN_LANG):
            print('Lang.json file not found!')
            sys.exit(1)
            
        self._bot: Bot = DiscordBot.create_bot(
            command_prefix='!!!!!!!!!!!',
            help_command=None,
            intents=discord.Intents.all()
        )
        self._logger_setup()
        load_language('en', FilePath.EN_LANG)
        set_language('en')
        self._start_bot()

    @logger.catch
    def _logger_setup(self) -> None:
        """Setup the logger."""
        logger.add(
            'debug.log',
            format='[{time:YYYY-MM-DD HH:mm:ss} {level} - {file}, {line}] ⮞ <level>{message}</level>',
            retention='16 days',
            rotation='12:00',
            enqueue=True
        )
      
    @logger.catch
    def _start_bot(self) -> None:
        """Start Discord Bot"""
        if BotConstants.TOKEN is None:
            logger.critical(translate_message('noToken'))
            sys.exit(1)
            
        self._bot.run(BotConstants.TOKEN)
