import os
from dataclasses import dataclass

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

@dataclass
class CategoriesConstants:
    try:
        TICKET_CATEGORY_ID = int(os.getenv('TICKET_CATEGORY_ID'))

    except TypeError:
        logger.critical('STAFF_ROLE_ID is not valid!')


@dataclass
class ChannelConstants:
    try:
        TICKET_LOGS_CHANNEL_ID: int = int(os.getenv('TICKET_LOGS_CHANNEL'))
        WELCOME_CHANNEL_ID: int = int(os.getenv('WELCOME_CHANNEL_ID'))

    except TypeError:
        logger.critical('STAFF_ROLE_ID is not valid!')


@dataclass
class RoleConstants:
    try:
        STAFF_ROLE_ID = int(os.getenv('STAFF_ROLE_ID'))

    except TypeError:
        logger.critical('STAFF_ROLE_ID is not valid!')
