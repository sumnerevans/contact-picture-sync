from getpass import getpass
import urllib.parse

import mechanicalsoup

from cps.stores.base import Contact
from .base import BaseRetriever, PersistentLoginInformation


class FacebookRetriever(BaseRetriever):
    FACEBOOK_BASE_URL = 'https://facebook.com'
    LOGIN_URL = f'{FACEBOOK_BASE_URL}/login'
    LOGIN_PATH = '/login'
    CHECKPOINT_PATH = '/checkpoint'
    TFA_FORM = 'u_0_a'
    REMEMBER_DEVICE_FORM = 'u_0_b'
    REVIEW_RECENT_LOGIN_FORM = 'u_0_9'
    FRIENDS_URL = f'{FACEBOOK_BASE_URL}/me/friends'
    HOMEPAGE_PATHS = ('/', '/home.php')

    def login(
        self,
        cached_login_info: PersistentLoginInformation,
    ) -> PersistentLoginInformation:
        print('Logging into Facebook...')

        self.browser = mechanicalsoup.StatefulBrowser()
        if cached_login_info.get('FacebookRetriever'):
            retriever_settings = cached_login_info.get('FacebookRetriever', {})
            self.browser.set_cookiejar(retriever_settings.get('cookiejar'))

        self.browser.open(self.LOGIN_URL)
        print(self._get_rel_path())

        while self._get_rel_path().startswith(self.LOGIN_PATH):
            self.browser.select_form()
            self.browser['email'] = input('Email or Phone Number: ')
            self.browser['pass'] = getpass()
            self.browser.submit_selected()

        while self._get_rel_path().startswith(self.CHECKPOINT_PATH):
            # Two-Factor Authentication page
            if self._form_exists(self.TFA_FORM):
                print('Found 2FA form')
                self.browser.select_form()
                self.browser['approvals_code'] = input(
                    'Enter your 6-digit two-factor authentication code: ')
                self.browser.submit_selected()

            # Remember Device page
            elif self._form_exists(self.REMEMBER_DEVICE_FORM):
                print('Submitting Remebmer Device form...')
                self.browser.select_form()
                self.browser['name_action_selected'] = 'dont_save'
                self.browser.submit_selected()

            # Review Recent Login page 1
            elif self._form_exists(self.REVIEW_RECENT_LOGIN_FORM):
                print('Submitting Review Recent Login form...')
                self.browser.select_form()
                btnName = None
                if self.browser.get_current_page().find_all(
                        'button[name="submit[This was me]"]'):
                    btnName = 'submit[This was me]'
                self.browser.submit_selected(btnName=btnName)
            else:
                # No idea what to do with this form.
                self.browser.launch_browser()
                break

        if self._get_rel_path() in self.HOMEPAGE_PATHS:
            print('Successfully logged in to Facebook.')
        else:
            print('FAILED LOGGING IN TO FACEBOOK!')
            self.browser.launch_browser()

        self.browser.open(self.FRIENDS_URL)
        self.browser.launch_browser()

        cached_login_info['FacebookRetriever'] = {
            'cookiejar': self.browser.get_cookiejar()
        }
        return cached_login_info

    def _get_rel_path(self) -> str:
        return urllib.parse.urlparse(self.browser.get_url()).path

    def _form_exists(self, id_: str) -> bool:
        return len(
            self.browser.get_current_page().find_all('form', id=id_)) > 0

    def retrieve(self, user: Contact):
        pass
