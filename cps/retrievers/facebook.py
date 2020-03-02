import urllib.parse
from getpass import getpass

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC

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

        firefox_binary = webdriver.firefox.firefox_binary.FirefoxBinary(
            '/usr/bin/firefox-nightly')
        self.browser: webdriver.Firefox = webdriver.Firefox(
            firefox_binary=firefox_binary)
        self.browser.get(self.LOGIN_URL)

        if cached_login_info:
            for cookie in cached_login_info.get('cookies', []):
                print(cookie)
                self.browser.add_cookie(cookie)
            self.browser.refresh()

        while self._get_rel_path().startswith(self.LOGIN_PATH):
            self.browser.find_element_by_id('email').send_keys(
                input('Email or Phone Number: '))
            self.browser.find_element_by_id('pass').send_keys(
                getpass() + Keys.ENTER)
            current_url = self.browser.current_url
            wait(self.browser, 15).until(EC.url_changes(current_url))

        while self._get_rel_path().startswith(self.CHECKPOINT_PATH):
            self.browser.implicitly_wait(1)
            disappeared = None
            # Two-Factor Authentication page
            if self._form_exists(self.TFA_FORM):
                print('Found 2FA form')
                self.browser.find_element_by_id('approvals_code').send_keys(
                    input(
                        'Enter your 6-digit two-factor authentication code: ')
                    + Keys.ENTER)
                disappeared = '#approvals_code'

            # Remember Device page
            elif self._form_exists(self.REMEMBER_DEVICE_FORM):
                print('Submitting Remebmer Device form...')
                self.browser.find_element_by_css_selector(
                    'input[type="radio"][value="dont_save"]').click()
                self.browser.find_element_by_id(
                    'checkpointSubmitButton').click()
                disappeared = 'input[type="radio"][value="dont_save"]'

            # Review Recent Login page 1
            elif self._form_exists(self.REVIEW_RECENT_LOGIN_FORM):
                print('Submitting Review Recent Login form...')
                try:
                    btn = self.browser.find_element_by_css_selector(
                        'button[name="submit[This was me]"]')
                except NoSuchElementException:
                    btn = self.browser.find_element_by_css_selector('button')
                    pass

                btn.click()
                disappeared = 'button[name="submit[This was me]"]'
            else:
                break

            # Wait for the page to change
            wait(self.browser, 15).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, disappeared)))

        self.browser.implicitly_wait(0)
        if self._get_rel_path() in self.HOMEPAGE_PATHS:
            print('Successfully logged in to Facebook.')
        else:
            print('FAILED LOGGING IN TO FACEBOOK!')
            return cached_login_info

        cached_login_info['cookies'] = self.browser.get_cookies()
        return cached_login_info

    def _get_rel_path(self) -> str:
        return urllib.parse.urlparse(self.browser.current_url).path

    def _form_exists(self, id_: str) -> bool:
        try:
            self.browser.find_element_by_css_selector(f'form#{id_}')
            return True
        except NoSuchElementException:
            return False

    def retrieve(self, user: Contact):
        self.browser.get(self.FRIENDS_URL)
        search_field = self.browser.find_element_by_css_selector(
            'input.inputtext[placeholder="Search for your friends"]')
        search_field.send_keys(user.name)
        wait(self.browser, 5).until(
            EC.text_to_be_present_in_element_value(
                (By.CSS_SELECTOR, 'div.fbProfileBrowserSummaryBox.phs.pvm'),
                user.name,
            ))

        result_list = self.browser.find_element_by_css_selector(
            'div.fbProfileBrowserListContainer')
        print(result_list)
        self.browser.find_element_by_css_selector
        print(result_list.())
