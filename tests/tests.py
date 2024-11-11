from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from bs4 import BeautifulSoup, element as bs24_element
from django.urls import reverse
from django.conf import settings
from django.http.response import HttpResponse
from django.contrib import auth
from base import models

from splinter import Browser, Config
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

from packaging.version import Version

import fair_debate_md as fdmd

from ipydex import IPS



class TestCore1(TestCase):
    fixtures = ["tests/testdata/users.json"]

    def post_to_view(self, viewname, **kwargs):

        response = self.client.get(reverse(viewname, kwargs=kwargs.get("view_kwargs", {})))
        self.assertEqual(response.status_code, 200)

        spec_values=kwargs.get("spec_values", {})

        post_data, action_url = generate_post_data_for_form(response, spec_values=spec_values)

        response = self.client.post(action_url, post_data)
        return response

    def perform_login(self, username=None, previous_response=None):

        username = username or "admin"

        if previous_response is None:
            previous_response = self.client.get(reverse("login"))
        self.assertFalse(auth.get_user(self.client).is_authenticated)
        login_data = {"username": username, "password": "admin"}
        post_data, action_url = generate_post_data_for_form(previous_response, spec_values=login_data)

        response = self.client.post(action_url, post_data)
        self.assertTrue(auth.get_user(self.client).is_authenticated)

        return response

    def perform_logout(self):
        response = self.client.get(reverse("logout"))
        self.assertFalse(auth.get_user(self.client).is_authenticated)
        return response

    def assertRedirectToLoginPage(self, response):
        self.assertEqual(response.status_code, 302)
        target_url = response["Location"]
        self.assertTrue(target_url.startswith(reverse("login")))

    def test_001__basics(self):
        self.assertGreaterEqual(Version(fdmd.__version__), Version("0.1.2"))

    def test_010__index(self):
        response = self.client.get(reverse("landingpage"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"utc_landingpage", response.content)

    def test_020__error(self):
        response = self.client.get(reverse("errorpage"))
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"utc_general_exception", response.content)
        self.assertIn(b"intentionally raised assertion error", response.content)

    def test_030__new_debate(self):
        response = self.client.get(reverse("new_debate"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"utc_new_debate", response.content)
        self.assertNotIn(b"utc_segmented_html", response.content)

        with open(fdmd.fixtures.txt1_md_fpath) as fp:
            content = fp.read()

        response = self.post_to_view(viewname="new_debate", spec_values={"body_content": content})
        self.assertIn(b"utc_segmented_html", response.content)


    def test_50__login_and_out(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(auth.get_user(self.client).is_authenticated)

        response = self.perform_login(previous_response=response)

        # redirect
        self.assertEqual(response.status_code, 302)
        new_url = response["Location"]
        response = self.client.get(new_url)

        self.assertTrue(auth.get_user(self.client).is_authenticated)

        self.perform_logout()

class TestGUI(StaticLiveServerTestCase):
    fixtures = ["tests/testdata/users.json"]
    # headless = False
    headless = True

    def setUp(self) -> None:
        self.options_for_browser = dict(driver_name='chrome')

        # docs: https://splinter.readthedocs.io/en/latest/config.html
        self.config_for_browser = Config(headless=self.headless)

        self.browsers = []

        return

    def tearDown(self):

        # quit all browser instances (also those which where not created by setUp)
        for browser in self.browsers:
            browser.quit()

    def get_browser_log(self, browser):
        res = browser.driver.get_log("browser")
        browser.logs.append(res)
        return res

    def visit(self, url, browser: Browser = None):
        if browser is None:
            # assume a browser has already been created
            browser = self.browsers[-1]
        browser.visit(f"{self.live_server_url}{url}")

    def perform_login(self, browser: Browser, username: str = "testuser"):
        self.visit(reverse("login"), browser=browser)
        pw = "admin"

        browser.find_by_id("id_username").fill(username)
        browser.find_by_id("id_password").fill(pw)
        browser.find_by_id("id_submit").click()


    def new_browser(self):
        """
        create and register a new browser

        :return: browser object and its index
        """
        chrome_options = Options()
        chrome_options.add_argument("--disable-search-engine-choice-screen")

        browser = Browser(**self.options_for_browser, config=self.config_for_browser, options=chrome_options)
        browser.logs = []
        self.browsers.append(browser)

        return browser

    def test_g01__get_landing_page(self):

        b1 = self.new_browser()
        url = reverse("landingpage")
        b1.visit(f"{self.live_server_url}{url}")

    def test_g02__dropdown(self):
        # get inspiration from radar
        pass


# #################################################################################################

# auxiliary functions:

# #################################################################################################


def send_key_to_browser(browser, key):
    actions = ActionChains(browser.driver)
    actions.send_keys(key)
    actions.perform()


def get_element_by_html_content(element_list: list, content: str):

    for elt in element_list:
        if elt.html == content:
            res_elt = elt
            return res_elt

    raise ValueError(f"Could not find element with content \"{content}\"")


# helper functions copied from moodpoll
def get_first_form(response):
    """
    Auxiliary function that returns a bs-object of the first form which is specifies by action-url.

    :param response:
    :return:
    """
    bs = BeautifulSoup(response.content, 'html.parser')
    forms = bs.find_all("form")

    form = forms[0]
    form.action_url = form.attrs.get("action")

    return form


def get_form_fields_to_submit(form):
    """
    Return two lists: fields and hidden_fields.

    :param form:
    :return:
    """

    inputs = form.find_all("input")
    textareas = form.find_all("textarea")

    post_fields = inputs + textareas

    types_to_omit = ["submit", "cancel"]

    fields = []
    hidden_fields = []
    for field in post_fields:
        ftype = field.attrs.get("type")
        if ftype in types_to_omit:
            continue

        if ftype == "hidden":
            hidden_fields.append(field)
        else:
            fields.append(field)

    return fields, hidden_fields


def generate_post_data_for_form(response_or_form, default_value="xyz", spec_values=None):
    """
    Return a dict containing all dummy-data for the form

    :param response_or_form:    form object or response object (-> first form is taken)
    :param default_value:       str; use this value for all not specified fields
    :param spec_values:         dict; use these values to override default value

    :return:                    dict of post_data
    """

    if isinstance(response_or_form, HttpResponse):
        form = get_first_form(response_or_form)
        original_url = response_or_form.request["PATH_INFO"]
    else:
        msg = "unexpectedly no form found"
        raise ValueError(msg)

    assert isinstance(form, bs24_element.Tag)
    assert form.name == "form"

    if form.action_url is None:
        action_url = original_url
    else:
        action_url = form.action_url

    if spec_values is None:
        spec_values = {}

    fields, hidden_fields = get_form_fields_to_submit(form)

    post_data = {}
    for f in hidden_fields:
        post_data[f.attrs['name']] = f.attrs['value']

    for f in fields:
        name = f.attrs.get('name')

        if name is None:
            # ignore fields without a name (relevant for dropdown checkbox)
            continue

        if name.startswith("captcha"):
            # special case for captcha fields (assume CAPTCHA_TEST_MODE=True)
            post_data[name] = "passed"
        else:
            post_data[name] = default_value

    post_data.update(spec_values)

    return post_data, action_url
