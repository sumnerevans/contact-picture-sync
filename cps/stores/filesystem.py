import io
from base64 import b64decode, b64encode
from pathlib import Path
from typing import List

import vobject
from PIL import Image

from .base import BaseStore, Contact, Photo, StoreSettings


class FilesystemStore(BaseStore):
    def __init__(self, settings: StoreSettings):
        self.filesystem_dirs: List[Path] = [
            Path(p)
            for p in settings.get('FilesystemStore', {}).get('paths', [])
        ]

    def __iter__(self):
        for directory in self.filesystem_dirs:
            for file in directory.iterdir():
                with open(file) as f:
                    try:
                        contact = vobject.readOne(f.read())
                    except Exception:
                        pass

                emails, tels, photo = [], [], ()
                for c in contact.getChildren():
                    if not c.value or c.value == '':
                        continue

                    if c.name.lower() == 'email':
                        emails.append(c.value)
                    elif c.name.lower() == 'tel':
                        tels.append(c.value)
                    elif c.name.lower() == 'photo':
                        if len(c.params) == 0:
                            # This means that the photo is a URL (which we
                            # don't care about)
                            continue

                        if c.params.get('VALUE', [None]) == ['URI']:
                            # The picture was in URI format. For now I don't
                            # care about that.
                            continue

                        photo = Photo(
                            c.params['ENCODING'],
                            c.params['TYPE'],
                            c.value,
                        )

                yield Contact(
                    file.absolute(),
                    contact.fn.value,
                    emails,
                    tels,
                    photo,
                )

    def prompt_replace(self, prompt_text: str) -> bool:
        while True:
            replace = input(prompt_text)
            if replace in ('', 'N', 'n'):
                return False
            if replace in ('Y', 'y'):
                return True

    def set_photo(self, contact: Contact, image_data: bytes):
        with open(contact.user_id) as cf:
            vcard = vobject.readOne(cf.read())

        image = Image.open(io.BytesIO(image_data))
        photos = [c for c in vcard.getChildren() if c.name.lower() == 'photo']

        if len(photos) == 1:
            # Check if the photo is the same.
            if image_data == photos[0].value:
                print('Photos are the same')
                return

            # If not the same, then check if user wants to override.
            if not self.prompt_replace(
                    f'Already have photo for {vcard.fn.value}. Replace? [y/N]: '
            ):
                return

        if len(photos) > 1:
            if not self.prompt_replace(
                    f'Multiple photos found for {vcard.fn.value}. Replace? [y/N]: '
            ):
                return

        # Remove all old photos:
        for child in photos:
            vcard.remove(child)

        photo = vcard.add('photo')
        photo.type_param = image.format
        photo.encoding_param = 'b'
        photo.value = image_data

        with open(contact.user_id, 'w+') as f:
            f.write(vcard.serialize())
