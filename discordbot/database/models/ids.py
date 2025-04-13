from dataclasses import dataclass


@dataclass
class IdObject:
    id: int
    object_id: int
    name: str
    type: str
