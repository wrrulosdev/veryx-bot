from typing import Optional

from discordbot import BotConstants
from rstatus import RStatusClient
from rstatus.models import JavaServerResponse

from loguru import logger


class ServerStatus:
    def __init__(self):
        self.domain: str = BotConstants.DOMAIN

    def get(self):
        client: RStatusClient = RStatusClient(target=self.domain)
        response: Optional[JavaServerResponse] = client.get_java_server_data()

        if response is None:
            logger.warning('Could not get data from server.')

        return response
