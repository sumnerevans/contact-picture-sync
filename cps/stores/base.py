from dataclasses import dataclass, field
from typing import List, Optional


class StoreSettings(dict):
    pass


@dataclass
class Photo:
    encoding: str
    type_: str
    data: bytes


@dataclass
class Contact:
    user_id: str
    name: str
    emails: List[str] = field(default_factory=list)
    _phone_numbers: List[str] = field(repr=False, default_factory=list)
    phone_numbers: List[str] = field(init=False, default_factory=list)
    photo: Optional[Photo] = None

    def __post_init__(self):
        def clean_phone_number(phone_number: str) -> str:
            cleaned = phone_number.replace(' ', '')
            cleaned = cleaned.replace('(', '')
            cleaned = cleaned.replace(')', '')
            cleaned = cleaned.replace('-', '')
            cleaned = cleaned.replace('+', '')
            return cleaned

        self.phone_numbers = list(map(clean_phone_number, self._phone_numbers))


class BaseStore():
    pass
