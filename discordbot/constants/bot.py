import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
PERMISSIONS_ROLE_ID = os.getenv('PERMISSIONS_ROLE_ID')


@dataclass
class BotConstants:
    COGS_PATH: str = 'discordbot/bot/cogs'
    COG_PATH: str = 'discordbot.bot.cogs'
    WELCOME_BACKGROUND_PATH: str = 'assets/welcome.jpg'
    TOKEN: Optional[str] = TOKEN
    PERMISSIONS_ROLE_ID = PERMISSIONS_ROLE_ID
    DB_FILENAME: str = 'database.db'
    AUTHOR: str = 'Veryx Network'
    DOMAIN: str = 'veryx.us'
