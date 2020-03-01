from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class StoreSettings(dict):
    pass


@dataclass
class Photo:
    encoding: str
    type_: str
    data: bytes


@dataclass
class Contact:
    source: str
    user_id: str
    name: str = None
    emails: List[str] = field(default_factory=list)
    _phone_numbers: List[str] = field(repr=False, default_factory=list)
    phone_numbers: List[str] = field(init=False, default_factory=list)
    photo: Photo = None

    def __post_init__(self):
        def clean_phone_number(phone_number):
            cleaned = phone_number.replace(' ', '')
            cleaned = cleaned.replace('(', '')
            cleaned = cleaned.replace(')', '')
            cleaned = cleaned.replace('-', '')
            cleaned = cleaned.replace('+', '')
            return cleaned

        self.phone_numbers = list(map(clean_phone_number, self._phone_numbers))

    def set_photo(self):
        raise NotImplementedError('`set_photo` is not implemented')


class BaseStore():
    pass
