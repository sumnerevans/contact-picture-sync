from pathlib import Path
from typing import List

import vobject

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
                    except:
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
                    'FilesystemStore',
                    file.stem,
                    contact.fn.value,
                    emails,
                    tels,
                    photo,
                )
