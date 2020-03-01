import argparse
import logging
import os
import pickle
from pathlib import Path

import cps.retrievers
import cps.stores
from cps.stores.base import StoreSettings


def main():
    parser = argparse.ArgumentParser(description='Contact Picture Sync')

    # TODO load from disk
    store_settings = StoreSettings()
    store_settings['FilesystemStore'] = {
        'paths':
        [os.path.expanduser('~/.local/share/vdirsyncer/contacts/contacts')]
    }

    retrievers = [r() for r in cps.retrievers.all_retrievers]
    stores = [s(store_settings) for s in cps.stores.all_stores]

    # TODO save login information, pull from cache if it exists. Pass existing
    # login info if it's cached so that the class can instantiate itself
    # without having to redo the auth.

    login_info = {}
    login_info_path = Path(
        '~/.local/share/contact-picture-sync/login_info.pickle').expanduser()
    login_info_path.parent.mkdir(parents=True, exist_ok=True)
    if login_info_path.exists():
        with open(login_info_path, 'rb') as f:
            try:
                login_info = pickle.load(f)
            except EOFError:
                pass

    login_information = {r.__class__: r.login(login_info) for r in retrievers}
    with open(login_info_path, 'wb+') as f:
        pickle.dump(login_information, f)

    for s in stores:
        for user in s:
            potential_photos = list(
                filter(
                    lambda x: x is not None,
                    [r.retrieve(user) for r in retrievers]))
            pass
