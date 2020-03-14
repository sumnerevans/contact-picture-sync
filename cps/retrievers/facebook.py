import os
import urllib.request
import urllib.parse
from getpass import getpass
from time import sleep
from typing import List, Optional

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

        self.browser.get(self.FRIENDS_URL)

        cached_login_info['cookies'] = self.browser.get_cookies()
        return cached_login_info

    def _get_rel_path(self) -> str:
        return urllib.parse.urlparse(self.browser.current_url).path

    def _form_exists(self, id_: str) -> bool:
        return self._find_element(f'form#{id_}') is not None

    def _compute_css_selectors(self, *path) -> str:
        css_selectors = []
        for element in path:
            selector = ''
            if type(element) == tuple:
                tag_type, props = element
                selector = tag_type + ''.join(
                    [f'[{k}="{v}"]' for k, v in props.items()])
            else:
                selector = element
            css_selectors.append(selector)

        return ' '.join(css_selectors)

    def _find_elements(
            self,
            *path,
    ) -> List[webdriver.firefox.webelement.FirefoxWebElement]:
        try:
            return self.browser.find_elements_by_css_selector(
                self._compute_css_selectors(*path))
        except NoSuchElementException:
            return []

    def _find_element(
        self,
        *path,
    ) -> Optional[webdriver.firefox.webelement.FirefoxWebElement]:
        try:
            return self.browser.find_element_by_css_selector(
                self._compute_css_selectors(*path))
        except NoSuchElementException:
            return None

    def retrieve(self, user: Contact) -> Optional[bytes]:
        if not self._get_rel_path().endswith('/friends'):
            self.browser.get(self.FRIENDS_URL)

        search_field = None
        i = 0
        while i < 100:
            try:
                search_field = self.browser.find_element_by_css_selector(
                    'input.inputtext[placeholder="Search for your friends"]')
                break
            except:
                sleep(0.3)
                i += 1

        if not search_field:
            return None

        # Search for the contact.
        search_field.send_keys(Keys.CONTROL + 'a')
        search_field.send_keys(user.name)
        sleep(0.3)
        wait(self.browser, 5).until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, 'div.fbProfileBrowserSummaryBox.phs.pvm'),
                # Sometimes there's spaces, and the search bar gets rid of them
                # in Facebook.
                user.name.split()[0],
            ))

        # If the contact was found, go to their profile.
        result_list = self._find_elements(
            'div.fbProfileBrowserListContainer', 'a.name')
        if len(result_list) == 1:
            current_url = self.browser.current_url
            result_list[0].click()
            wait(self.browser, 15).until(EC.url_changes(current_url))
            wait(self.browser, 15).until(
                EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, '#fb-timeline-cover-name a'),
                    user.name.split()[0],
                ))
            sleep(0.5)

            profile_image_thumb = None
            while profile_image_thumb is None:
                profile_image_thumb = self._find_element(
                    '#fbProfileCover',
                    'a.profilePicThumb',
                    'img',
                )
                sleep(0.2)

            self.browser.execute_script(
                'arguments[0].click()', profile_image_thumb)

            profile_image = None
            try:
                wait(self.browser, 15).until(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            self._compute_css_selectors(
                                '#photos_snowlift',
                                ('img.spotlight', {
                                    'aria-busy': 'false'
                                }),
                            ))))
                profile_image = self._find_element(
                    '#photos_snowlift',
                    ('img.spotlight', {
                        'aria-busy': 'false'
                    }),
                )
            except:
                pass

            if not profile_image:
                return None

            try:
                return urllib.request.urlopen(
                    profile_image.get_attribute('src')).read()
            except Exception:
                pass

        return None
