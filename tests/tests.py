import os
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
from base import models

from ipydex import IPS

class Container:
    pass


class TestCore1(TestCase):
    fixtures = ["tests/testdata/fixtures01.json"]

    def post_to_view(self, viewname, **kwargs):

        response = self.client.get(reverse(viewname, kwargs=kwargs.get("view_kwargs", {})))
        self.assertEqual(response.status_code, 200)

        spec_values = kwargs.get("spec_values", {})

        post_data, action_url = generate_post_data_for_form(response, spec_values=spec_values)

        response = self.client.post(action_url, post_data)
        return response

    def perform_login(self, username=None, previous_response=None, next_url=None, logout_first=True):
        """

        :param next_url:    only evaluated if previous_response is None
        """

        if logout_first:
            self.perform_logout()

        username = username or "admin"

        if previous_response is None:
            url = reverse("login")
            if next_url:
                # construct something like /login/?next=/show/test
                url = f"{url}?next={next_url}"
            previous_response = self.client.get(url)
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
        self.assertGreaterEqual(Version(fdmd.__version__), Version("0.2.0"))

    def test_010__index(self):
        response = self.client.get(reverse("landingpage"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"utc_landingpage", response.content)

    def test_020__error(self):
        response = self.client.get(reverse("errorpage"))
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"utc_general_exception", response.content)
        self.assertIn(b"intentionally raised assertion error", response.content)

        # provoke 404
        response = self.client.get("/does/not/exist")
        self.assertIn(b"utc_404_error", response.content)
        self.assertEqual(response.status_code, 404)

    def test_030__new_debate(self):
        response = self.client.get(reverse("new_debate"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"utc_new_debate", response.content)
        self.assertNotIn(b"utc_segmented_html", response.content)

        with open(fdmd.fixtures.txt1_md_fpath) as fp:
            content = fp.read()

        response = self.post_to_view(viewname="new_debate", spec_values={"body_content": content})
        self.assertIn(b"utc_segmented_html", response.content)

    def test_050__login_and_out(self):
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
        response = self.perform_login()
        self.assertEqual(response.status_code, 302)
        new_url = response["Location"]
        self.assertEqual(new_url, reverse("landingpage"))
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)

        self.perform_logout()

        # test if redirect with ?next=... works
        response = self.perform_login(next_url=reverse("test_show_debate"))
        self.assertEqual(response.status_code, 302)
        new_url = response["Location"]
        self.assertEqual(new_url, reverse("test_show_debate"))

    def _06x__common(self) -> Container:

        # ensure file system based test data exists:

        TEST_REPO1_PATH = os.path.join(settings.REPO_HOST_DIR, fdmd.TEST_DEBATE_KEY, ".git")
        if not os.path.isdir(TEST_REPO1_PATH):
            raise FileNotFoundError(TEST_REPO1_PATH)

        settings.CATCH_EXCEPTIONS = False

        url = reverse("test_show_debate")
        response = self.client.get(url)

        # if this fails, probably ./content_repos is not initialized
        # solution: `fdmd unpack-repos ./content_repos``
        self.assertEqual(response.status_code, 200)
        res = Container()
        res.action_url, csrf_token = get_form_base_data_from_html_template_host(response.content)

        res.post_data_a3 = {
            "csrfmiddlewaretoken": csrf_token,
            # hard coded data
            "reference_segment": "a3",
            "debate_key": fdmd.TEST_DEBATE_KEY,
            "body": "This is a level 1 **answer** from a unittest.",
        }

        res.post_data_a3_updated = res.post_data_a3.copy()
        res.post_data_a3_updated.update({"body": "This is an updated level 1 **answer** from a unittest.",})

        res.post_data_a4b4 = res.post_data_a3.copy()
        res.post_data_a4b4.update({
            "reference_segment": "a4b4",
            "body": "This is a level 2 *answer* from a unittest.",
        })

        res.debate_obj1 = models.Debate.objects.get(debate_key=fdmd.TEST_DEBATE_KEY)


        return res

    def test_060__add_answer_level1_without_login(self):
        c = self._06x__common()

        response = self.client.post(c.action_url, c.post_data_a3)
        self.assertEqual(response.status_code, 302)
        new_url = response["Location"]
        self.assertTrue(new_url.startswith("/login"))
        response = self.client.get(new_url)

    def test_061__add_answer_level1(self):
        c = self._06x__common()

        # first wrong user
        response = self.perform_login(username="testuser_1")
        response = self.client.post(c.action_url, c.post_data_a3)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"utc_contribution_with_wrong_mode_not_allowed_for_user", response.content)

        # second wrong user
        response = self.perform_login(username="testuser_3", logout_first=True)
        response = self.client.post(c.action_url, c.post_data_a3)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"utc_no_contribution_allowed_for_user", response.content)

        # correct user
        self.assertEqual(len(c.debate_obj1.contribution_set.all()), 0)
        self.perform_login(username="testuser_2", logout_first=True)
        response = self.client.post(c.action_url, c.post_data_a3)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(c.debate_obj1.contribution_set.all()), 1)
        soup = BeautifulSoup(response.content, "html.parser")
        answer_div = soup.find(id="answer_a3b")
        self.assertIsNotNone(answer_div)
        segment_span = answer_div.find(id="a3b1")
        self.assertIsNotNone(segment_span)

        expected_res = "This is a level 1\n     <strong>\n      answer\n     </strong>\n     from a unittest."
        res = "".join(map(str, segment_span.contents)).strip()
        self.assertEqual(res, expected_res)

        # we are still testuser_2
        # send data for that segment key again with different body (update post)
        response = self.client.post(c.action_url, c.post_data_a3_updated)

        # ensure that no additional object is created
        self.assertEqual(len(c.debate_obj1.contribution_set.all()), 1)
        expected_res = (
            "This is an updated level 1\n     <strong>\n      answer\n     </strong>\n     from a unittest."
        )

        soup = BeautifulSoup(response.content, "html.parser")
        segment_span = soup.find(id="a3b1")
        res = "".join(map(str, segment_span.contents)).strip()
        self.assertEqual(res, expected_res)


    def test_062__add_answer__level2(self):
        c = self._06x__common()

        # first wrong user (testuser_2 which has role b)
        response = self.perform_login(username="testuser_2")
        response = self.client.post(c.action_url, c.post_data_a4b4)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"utc_contribution_with_wrong_mode_not_allowed_for_user", response.content)

        # second wrong user (testuser_3 has no role at all here)
        response = self.perform_login(username="testuser_3", logout_first=True)
        response = self.client.post(c.action_url, c.post_data_a4b4)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"utc_no_contribution_allowed_for_user", response.content)

        # correct user (testuser_1 which has role a)
        response = self.perform_login(username="testuser_1", logout_first=True)
        response = self.client.post(c.action_url, c.post_data_a4b4)
        self.assertEqual(len(c.debate_obj1.contribution_set.all()), 1)
        expected_res = (
            "This is a level 2\n        <em>\n         answer\n        </em>\n        from a unittest."
        )

        soup = BeautifulSoup(response.content, "html.parser")
        segment_span = soup.find(id="a4b4a1")
        res = "".join(map(str, segment_span.contents)).strip()
        self.assertEqual(res, expected_res)


def get_form_base_data_from_html_template_host(response_content: bytes) -> str:
    """
    This function expects that the csrf token is available within a template-tag with a special
    id.

    Motivation: for dynamically created forms it is not possible to generate the post data the usual way.
    This function helps to create it manually.
    """
    soup = BeautifulSoup(response_content, "html.parser")
    template_tag = soup.find(id="form_base_data_host")
    action_url = template_tag.attrs["data-action-url"]
    csrf_token = template_tag.find("input").attrs["value"]

    return action_url, csrf_token


class TestGUI(StaticLiveServerTestCase):
    fixtures = ["tests/testdata/fixtures01.json"]
    # headless = False
    headless = True

    def setUp(self) -> None:
        self.options_for_browser = dict(driver_name="chrome")

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

    def perform_login(self, browser: Browser, username: str = "testuser_1"):
        self.visit(reverse("login"), browser=browser)
        pw = "admin"

        browser.find_by_id("id_username").fill(username)
        browser.find_by_id("id_password").fill(pw)
        browser.find_by_id("id_submit").click()

        # ensure that the login was successful

        failed_login_attempt = self.fast_get_by_id(browser, id_str="data-failed_login_attempt")

        if failed_login_attempt and failed_login_attempt.html == "true":
            msg = f"Login process unexpectedly failed ({username=})"
            raise ValueError(msg)

    def fast_get_by_id(self, browser: Browser, id_str: str):
        """
        This function is faster in cases where the
        """
        js_get_data = f'document.getElementById("{id_str}")'
        js_res = browser.evaluate_script(js_get_data)
        if not js_res:
            return None
        else:
            return browser.find_by_id(id_str)[0]

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
        # TODO: get inspiration from radar
        pass

    def test_g03__segment_answer1(self):

        # for test development
        # self.config_for_browser.headless = False
        b1 = self.new_browser()
        url = reverse("test_show_debate")
        b1.visit(f"{self.live_server_url}{url}")

        # assert that no form is displayed:
        # (using JS is faster and more reliable than using splinter directly)

        js_segment_answer_forms = 'document.getElementsByClassName("segment_answer_form_container")'
        self.assertEqual(len(b1.evaluate_script(js_segment_answer_forms)), 0)

        # assert that the form has appeared
        b1.find_by_id("a3").click()
        self.assertEqual(len(b1.evaluate_script(js_segment_answer_forms)), 1)

        # assert that the form does not appear multiple times
        b1.find_by_id("a3").click()
        self.assertEqual(len(b1.evaluate_script(js_segment_answer_forms)), 1)

        b1.find_by_id("a3").click()
        self.assertEqual(len(b1.evaluate_script(js_segment_answer_forms)), 1)

        # cancel the form
        b1.find_by_css("._cancel_button").click()
        self.assertEqual(len(b1.evaluate_script(js_segment_answer_forms)), 0)

        b1.find_by_id("a3").click()
        self.assertEqual(len(b1.evaluate_script(js_segment_answer_forms)), 1)

        form = b1.find_by_id("segment_answer_form")[0]
        ta = form.find_by_tag("textarea")[0]
        ta.type("This is an answer from a unittest.")
        form.find_by_css("._submit_button").click()

        ## assert that post is only possible if logged in
        self.assertTrue(b1.url.startswith(f"{self.live_server_url}/login"))

    def test_g04__segment_answer2(self):

        # self.config_for_browser.headless = False

        b1 = self.new_browser()
        self.perform_login(browser=b1)
        url = reverse("test_show_debate")
        b1.visit(f"{self.live_server_url}{url}")

        b1.find_by_id("a3").click()

        form = b1.find_by_id("segment_answer_form")[0]
        ta = form.find_by_tag("textarea")[0]
        ta.type("This is an answer from a unittest.")
        form.find_by_css("._submit_button").click()

        # check result
        answer_div = b1.find_by_id("answer_a3b")
        self.assertNotEqual(answer_div, [])
        segment_span = answer_div.find_by_id("a3b1")[0]
        self.assertNotEqual(segment_span, [])

        content = segment_span.html.strip()
        expected_res = "This is an answer from a unittest."
        self.assertEqual(content, expected_res)


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

    raise ValueError(f'Could not find element with content "{content}"')


# helper functions copied from moodpoll
def get_first_form(response):
    """
    Auxiliary function that returns a bs-object of the first form which is specifies by action-url.

    :param response:
    :return:
    """
    bs = BeautifulSoup(response.content, "html.parser")
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
        post_data[f.attrs["name"]] = f.attrs["value"]

    for f in fields:
        name = f.attrs.get("name")

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
