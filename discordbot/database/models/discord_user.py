from dataclasses import dataclass


@dataclass
class DiscordUser:
    discord_id: int
    username: str
    joined_at: str
