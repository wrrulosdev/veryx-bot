import os
from dataclasses import dataclass


@dataclass
class FilePath:
    EN_LANG: str = os.path.join('languages', 'en.json')