import os
import json
import time
import unittest

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.conf import settings
from django.http.response import HttpResponse
from django.contrib import auth

# from bs4 import BeautifulSoup, element as bs24_element

from splinter import Browser, Config
from splinter.driver.webdriver import BaseWebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

from ipydex import IPS
import fair_debate_md as fdmd
from base import models


from .utils import (
    logger,
    Container,
    RepoResetMixin,
    REPO_HOST_DIR,
    N_CTB_IN_FIXTURES,
    N_DEBATES_IN_FIXTURES,
    N_COMMITS_TEST_REPO,
    get_parsed_element_by_id,
)

pjoin = os.path.join


class TestGUI(RepoResetMixin, StaticLiveServerTestCase):
    fixtures = ["tests/testdata/fixtures01.json"]
    # headless = True
    headless = "new"  # recommended by ai

    js_segment_contribution_forms = 'document.getElementsByClassName("segment_contribution_form_container")'

    @classmethod
    def setUpClass(cls):
        # this is necessary to handle the fixtures
        super().setUpClass()
        logger.info(f"start of TestClass `{cls}`")

    @classmethod
    def tearDownClass(cls):
        logger.info(f"end of TestClass `{cls}`")

    def setUp(self) -> None:
        self.set_up()
        # docs: https://splinter.readthedocs.io/en/latest/config.html
        self.browsers = []
        self.repo_dir1 = os.path.join(settings.REPO_HOST_DIR, fdmd.TEST_DEBATE_KEY)

    def tearDown(self):
        self.tear_down()

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

        failed_login_attempt = self.fast_get(browser, id_str="data-failed_login_attempt")

        if failed_login_attempt and failed_login_attempt.html == "true":
            msg = f"Login process unexpectedly failed ({username=})"
            raise ValueError(msg)

    def perform_logout(self, browser: BaseWebDriver):
        browser.visit(f"{self.live_server_url}{reverse('logout')}")
        self.assertFalse(auth.get_user(self.client).is_authenticated)

    def fast_get(self, browser: Browser, id_str: str = None, class_str: str = None):
        """
        Look with JS if the item is present, then return it as splinter object.

        This function is faster in cases where the item could not be found.

        If both id_str and class_str are given, then class-based selection is applied to the
        children of the element specified by id_str
        """

        assert not ((id_str is None) and (class_str is None))

        if id_str is not None:
            js_get_data = f'document.getElementById("{id_str}")'
        else:
            js_get_data = "document"

        if class_str is not None:
            js_get_data = f'{js_get_data}.getElementsByClassName("{class_str}")'

        js_res = browser.evaluate_script(js_get_data)
        if not js_res:
            return None
        else:
            if id_str is not None:
                res = browser.find_by_id(id_str)[0]
            else:
                res = browser
            if class_str:
                res = res.find_by_css(f".{class_str}")
            return res

    def new_browser(self):
        """
        create and register a new browser

        :return: browser object and its index
        """
        chrome_options = Options()
        chrome_options.add_argument("--disable-search-engine-choice-screen")
        if self.headless:
            chrome_options.add_argument("--headless=new")

        browser = Browser("chrome", options=chrome_options)
        browser.logs = []
        self.browsers.append(browser)

        return browser

    def test_g01__get_error_free_landing_page(self):

        # self.headless = False

        b1 = self.new_browser()
        url = reverse("landing_page")
        b1.visit(f"{self.live_server_url}{url}")
        utd = get_parsed_element_by_id(id="data-utd_page_type", browser=b1)
        self.assertEqual(utd, "utd_landing_page")
        self.assertFalse(get_js_error_list(b1))

        url = reverse("trigger_js_error")
        b1.visit(f"{self.live_server_url}{url}")

        js_errors = get_js_error_list(b1)
        self.assertEqual(len(js_errors), 1)
        self.assertIn("Uncaught ReferenceError: notExistingVariable is not defined", js_errors[0]["message"])

    def test_g02__dropdown(self):
        # TODO: get inspiration from radar
        pass

    def test_g031__segment_clicks_for_anonymous_or_no_role_user(self):

        # for test development
        # self.headless = False

        b1 = self.new_browser()

        def _test_procedure():
            b1.visit(f"{self.live_server_url}{reverse('test_show_debate')}")

            # assert that no form is displayed:
            # (using JS is faster and more reliable than using splinter directly)
            self.assertEqual(len(b1.evaluate_script(self.js_segment_contribution_forms)), 0)

            seg_id_text_0 = b1.find_by_id("seg_id_display")[0].text
            self.assertEqual(seg_id_text_0, "")

            # note: we use this hack to work around problems in headless mode
            trigger_mouseover_event(b1, id="a3")
            seg_id_text_1 = b1.find_by_id("seg_id_display")[0].text
            self.assertEqual(seg_id_text_1, "a3")

            self.assertIsNone(self.fast_get(browser=b1, id_str=None, class_str="separator_widget"))

            # the segment-toolbar with copy-url-widget should appear
            b1.find_by_id("a3").click()
            separator_div = self.fast_get(browser=b1, id_str=None, class_str="separator_widget")
            self.assertIn("#a3", separator_div.find_by_css("._text").html)

            # click again to hide it
            b1.find_by_id("a3").click()
            self.assertIsNone(self.fast_get(browser=b1, id_str=None, class_str="separator_widget"))

            # now test that elements appear
            trigger_mouseover_event(b1, id="a2")
            seg_id_text_1 = b1.find_by_id("seg_id_display")[0].text
            self.assertEqual(b1.find_by_id("seg_id_display")[0].text, "a2")

            # get_js_visibility_for_id(b1,
            self.assertFalse(get_js_visibility_for_id(b1, "contribution_a2b"))
            trigger_click_event(b1, id="a2")

            self.assertTrue(get_js_visibility_for_id(b1, "contribution_a2b"))

            # investigate child contribution
            self.assertFalse(get_js_visibility_for_id(b1, "contribution_a2b1a"))
            trigger_click_event(b1, id="a2b1")
            self.assertTrue(get_js_visibility_for_id(b1, "contribution_a2b1a"))

            self.assertFalse(get_js_visibility_for_id(b1, "contribution_a2b1a3b"))
            trigger_click_event(b1, id="a2b1a3")

            self.assertTrue(get_js_visibility_for_id(b1, "contribution_a2b1a3b"))
            separator_div = self.fast_get(browser=b1, id_str=None, class_str="separator_widget")
            self.assertIn("a2b1a3", separator_div.find_by_css("._text").html)

            # hide widgets again
            trigger_click_event(b1, id="a2b1a3")
            self.assertIsNone(b1.evaluate_script("activeSegmentToolbar"))
            self.assertIsNone(self.fast_get(browser=b1, id_str=None, class_str="separator_widget"))

            # also test for non-appearance of contribution dialog after child segment click
            trigger_mouseover_event(b1, id="a2b1a3b1")
            self.assertEqual(b1.find_by_id("seg_id_display")[0].text, "a2b1a3b1")

            # assert that a click on it only shows segment toolbar but no contribution dialog
            self.assertIsNone(self.fast_get(browser=b1, id_str=None, class_str="separator_widget"))
            self.assertIsNone(self.fast_get(b1, class_str="segment_contribution_form_container"))
            trigger_click_event(b1, id="a2b1a3b1")

            separator_div = self.fast_get(browser=b1, id_str=None, class_str="separator_widget")
            self.assertIn("#a2b1a3b1", separator_div.find_by_css("._text").html)
            self.assertIsNone(self.fast_get(b1, class_str="segment_contribution_form_container"))

            # end of def _test_procedure

        # test desired behavior for anonymous user
        _test_procedure()

        # the same behavior should occur for no-role-user
        self.perform_login(browser=b1, username="testuser_3")
        _test_procedure()

    def test_g032__gui_behavior_for_users(self):

        # self.headless = False
        b1 = self.new_browser()

        # testuser_2 (role b)
        self.perform_login(browser=b1, username="testuser_2")
        b1.visit(f"{self.live_server_url}{reverse('test_show_debate')}")

        # for existing committed element
        self.assertIsNone(self.fast_get(b1, "segment_contribution_hint_container"))

        # side quest: check if `unfoldAllUncommittedContributions` worked
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a2b"))
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a2b1a"))
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a2b1a1b"))

        # investigate the (non) appearance of the contribution form
        # (this is not solved via `self.fast_get_by_id` to possibly receive more then 1 result)
        js_segment_contribution_forms = (
            'document.getElementsByClassName("segment_contribution_form_container")'
        )
        self.assertEqual(len(b1.evaluate_script(js_segment_contribution_forms)), 0)

        trigger_click_event(b1, id="a3")
        self.assertEqual(len(b1.evaluate_script(js_segment_contribution_forms)), 1)

        # assert that the form does not appear multiple times
        trigger_click_event(b1, id="a3")
        self.assertEqual(len(b1.evaluate_script(js_segment_contribution_forms)), 1)

        trigger_click_event(b1, id="a3")
        self.assertEqual(len(b1.evaluate_script(js_segment_contribution_forms)), 1)

        # cancel the form
        b1.find_by_css("._cancel_button").click()
        self.assertEqual(len(b1.evaluate_script(js_segment_contribution_forms)), 0)

        trigger_click_event(b1, id="a3")
        self.assertEqual(len(b1.evaluate_script(js_segment_contribution_forms)), 1)

        # fill and submit the form
        form = b1.find_by_id("segment_contribution_form")[0]
        ta = form.find_by_tag("textarea")[0]

        # ensure that the submit button is disabled
        submit_button = self.fast_get(browser=b1, id_str="submit_btn_contribution_a3b")
        self.assertEqual(submit_button["disabled"], "true")

        msg_content0 = "ABC"
        ta.type(msg_content0)
        self.assertEqual(ta.value, msg_content0)
        self.assertIsNone(submit_button["disabled"])

        # ta.clear() # this does not trigger the callback
        send_key_to_browser(b1, Keys.BACKSPACE, n=3)
        self.assertEqual(ta.value, "")
        self.assertEqual(submit_button["disabled"], "true")
        msg_content1 = "This is an answer from a unittest."
        ta.type(msg_content1)
        self.assertIsNone(submit_button["disabled"])

        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES)
        # form.find_by_css("._submit_button").click()
        submit_button.click()
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES + 1)

        # test for new element (should be visible by default)
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a3b"))
        trigger_click_event(b1, id="a3")
        self.assertFalse(get_js_visibility_for_id(b1, "contribution_a3b"))
        trigger_click_event(b1, id="a3")
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a3b"))

        trigger_mouseover_event(b1, id="a3b1")

        self.assertIsNone(self.fast_get(b1, "segment_contribution_hint_container"))
        # this should currently trigger a warning in the future an edit-dialog
        trigger_click_event(b1, id="a3b1")

        # no form should open:
        self.assertEqual(len(b1.evaluate_script(js_segment_contribution_forms)), 0)

        # test that the new contribution is displayed in response to get request
        b1.visit(f"{self.live_server_url}{reverse('landing_page')}")  # goto unrelated url
        b1.visit(f"{self.live_server_url}{reverse('test_show_debate')}")
        self.assertIsNotNone(self.fast_get(b1, "a3b1"))

        # test updating of new contribution

        contribution_div = b1.find_by_id("contribution_a3b")
        separator_div = contribution_div.find_by_css(".separator_widget")[0]
        # self.assertTrue(separator_div.is_visible())
        self.assertTrue(separator_div.is_visible())
        edit_button = separator_div.find_by_css("._edit_button")[0]

        # form does not exist until edit-button is pressed
        self.assertIsNone(self.fast_get(b1, "segment_contribution_form_container"))
        edit_button.click()

        form_container_div = contribution_div.find_by_css(".segment_contribution_form_container")[0]
        self.assertTrue(form_container_div.is_visible())

        form = b1.find_by_id("segment_contribution_form")[0]
        ta = form.find_by_tag("textarea")[0]
        self.assertEqual(ta.html, msg_content1)
        ta.type("\n\nNow with one **more** line!")
        form.find_by_css("._submit_button").click()
        trigger_click_event(b1, id="a3")
        contribution_div = b1.find_by_id("contribution_a3b")[0]

        self.assertEqual(len(contribution_div.find_by_css(".p_level1")), 2)
        paragraph1 = contribution_div.find_by_css(".p_level1")[0].html.strip()
        paragraph1_exp = (
            '<span class="segment" id="a3b1">\n     This is an answer from a unittest.\n    </span>'
        )
        self.assertEqual(paragraph1, paragraph1_exp)

        paragraph2 = contribution_div.find_by_css(".p_level1")[1].html.strip()
        paragraph2_exp = (
            '<span class="segment" id="a3b2">\n     Now with one\n     '
            "<strong>\n      more\n     </strong>\n     line!\n    </span>"
        )
        self.assertEqual(paragraph2, paragraph2_exp)

        #
        # end of testuser_2 phase
        #

        # new contribution should not be contained in response for anonymous user
        self.perform_logout(b1)
        b1.visit(f"{self.live_server_url}{reverse('test_show_debate')}")
        self.assertIsNone(self.fast_get(b1, "a3b1"))

        #
        # testuser_1 phase (role a)
        #
        # for testuser_1 segment a3b1 should also not be present
        self.perform_login(browser=b1, username="testuser_1")

        b1.visit(f"{self.live_server_url}{reverse('test_show_debate')}")
        self.assertIsNone(self.fast_get(b1, "a3b1"))

        # testuser_1 should be able to answer to a2b2
        trigger_click_event(b1, id="a2")  # open existing answer
        self.assertEqual(len(b1.evaluate_script(js_segment_contribution_forms)), 0)
        trigger_click_event(b1, id="a2b2")

        # does the form appear as expected?
        self.assertEqual(len(b1.evaluate_script(js_segment_contribution_forms)), 1)
        trigger_click_event(b1, id="cancel_btn_contribution_a2b2a")

        trigger_click_event(b1, id="a3")
        # no form should open:
        self.assertEqual(len(b1.evaluate_script(js_segment_contribution_forms)), 0)

    def test_g040__segment_contribution_level1(self):
        """
        This test somewhat overlaps with g032 but is useful for development (faster)
        """

        # self.headless = False

        b1 = self.new_browser()
        self.perform_login(browser=b1, username="testuser_2")
        b1.visit(f"{self.live_server_url}{reverse('test_show_debate')}")

        b1.find_by_id("a3").click()

        form = b1.find_by_id("segment_contribution_form")[0]
        ta = form.find_by_tag("textarea")[0]
        ta.type("This is an answer from a unittest.")
        form.find_by_css("._submit_button").click()

        # check result
        contribution_div = b1.find_by_id("contribution_a3b")
        self.assertNotEqual(contribution_div, [])
        segment_span = contribution_div.find_by_id("a3b1")[0]
        self.assertNotEqual(segment_span, [])

        content = segment_span.html.strip()
        expected_res = "This is an answer from a unittest."
        self.assertEqual(content, expected_res)

        user_role_element = b1.find_by_id("data-user_role")[0]
        user_role = json.loads(user_role_element.html)
        self.assertEqual(user_role, "b")

    def test_g050__segment_contribution_form_toggling(self):

        # self.headless = False
        b1 = self.new_browser()

        # testuser_2 -> role b
        self.perform_login(browser=b1, username="testuser_2")
        b1.visit(f"{self.live_server_url}{reverse('test_show_debate')}")

        js_segment_contribution_forms = (
            'document.getElementsByClassName("segment_contribution_form_container")'
        )
        self.assertEqual(len(b1.evaluate_script(js_segment_contribution_forms)), 0)

        b1.find_by_id("a8").click()
        self.assertEqual(len(b1.evaluate_script(js_segment_contribution_forms)), 1)
        form_container_div = b1.find_by_id("segment_contribution_form_container")
        # check data attribute
        self.assertEqual(form_container_div["data-related_segment"], "a8")

        b1.find_by_id("a9").click()
        form_container_div = b1.find_by_id("segment_contribution_form_container")
        self.assertEqual(form_container_div["data-related_segment"], "a9")

        # reactivate the form which we deactivated before
        b1.find_by_id("a8").click()
        form_container_div = b1.find_by_id("segment_contribution_form_container")
        self.assertEqual(form_container_div["data-related_segment"], "a8")

        # now we make use of the db_contribution from the fixtures
        # should be already visible (contains uncommitted contribution)
        contribution_div_id = "contribution_a15b"
        contribution_div = b1.find_by_id(contribution_div_id)
        self.assertTrue(get_js_visibility_for_id(b1, contribution_div_id))
        edit_button = contribution_div.find_by_css("._edit_button")[0]
        edit_button.click()
        form_container_div = b1.find_by_id("segment_contribution_form_container")
        self.assertEqual(form_container_div["data-related_segment"], "a15")

        trigger_click_event(b1, id="a8")
        # b1.find_by_id("a8").click()  # does somehow not work in headless mode
        form_container_div = b1.find_by_id("segment_contribution_form_container")
        self.assertEqual(form_container_div["data-related_segment"], "a8")

    def test_g080__commit_contribution1(self):

        # self.headless = False
        b1 = self.new_browser()

        self.mark_repo_for_reset(self.repo_dir1)

        nbr_of_commits = fdmd.utils.get_number_of_commits(repo_dir=self.repo_dir1)
        self.assertEqual(nbr_of_commits, N_COMMITS_TEST_REPO)

        # testuser_2 -> role b
        self.perform_login(browser=b1, username="testuser_2")
        b1.visit(f"{self.live_server_url}{reverse('test_show_debate')}")

        def _test_procedure(contribution_div_id: str, delta0: int):
            contribution_div = b1.find_by_id(contribution_div_id)
            self.assertTrue(get_js_visibility_for_id(b1, contribution_div_id))
            self.assertIn("db_ctb", contribution_div["class"])

            self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES - delta0)

            # workaround for headless problem with .click()
            trigger_click_event(b1, f'commit_btn_{contribution_div["id"]}')

            # this might depend on the test-hardware
            time.sleep(1)

            self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES - delta0 - 1)

            nbr_of_commits = fdmd.utils.get_number_of_commits(repo_dir=self.repo_dir1)
            self.assertEqual(nbr_of_commits, N_COMMITS_TEST_REPO + delta0 + 1)

            contribution_div_new = b1.find_by_id(contribution_div_id)
            self.assertNotIn("db_ctb", contribution_div_new["class"])

        _test_procedure("contribution_a15b", delta0=0)
        _test_procedure("contribution_a2b1a1b", delta0=1)

    def test_g081__commit_all_contribution(self):
        # self.headless = False
        b1 = self.new_browser()
        self.mark_repo_for_reset(self.repo_dir1)
        self.perform_login(browser=b1, username="testuser_2")
        b1.visit(f"{self.live_server_url}{reverse('test_show_debate')}")

        db_ctb_divs = b1.find_by_css(".db_ctb")
        self.assertEqual(len(db_ctb_divs), N_CTB_IN_FIXTURES)

        # workaround for headless problem with .click()
        trigger_click_event(b1, "btn_commit_all_ctbs")
        time.sleep(0.5)

        self.assertEqual(len(models.Contribution.objects.all()), 0)

        nbr_of_commits = fdmd.utils.get_number_of_commits(repo_dir=self.repo_dir1)
        self.assertEqual(nbr_of_commits, N_COMMITS_TEST_REPO + 1)

        db_ctb_divs = b1.find_by_css(".db_ctb")
        self.assertEqual(len(db_ctb_divs), 0)

    def test_g090__delete_contribution1(self):

        # self.headless = False
        b1 = self.new_browser()

        nbr_of_commits = fdmd.utils.get_number_of_commits(repo_dir=self.repo_dir1)
        self.assertEqual(nbr_of_commits, N_COMMITS_TEST_REPO)

        # testuser_2 -> role b
        self.perform_login(browser=b1, username="testuser_2")
        b1.visit(f"{self.live_server_url}{reverse('test_show_debate')}")

        def _test_procedure(contribution_div_id: str, delta0: int):
            contribution_div = b1.find_by_id(contribution_div_id)
            self.assertTrue(get_js_visibility_for_id(b1, contribution_div_id))
            self.assertIn("db_ctb", contribution_div["class"])

            self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES - delta0)

            # workaround for headless problem with .click()
            trigger_click_event(b1, f'delete_btn_{contribution_div["id"]}')

            # this might depend on the test-hardware
            time.sleep(0.3)

            self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES - delta0 - 1)

            nbr_of_commits = fdmd.utils.get_number_of_commits(repo_dir=self.repo_dir1)
            self.assertEqual(nbr_of_commits, N_COMMITS_TEST_REPO)

            contribution_div_new = self.fast_get(b1, contribution_div_id)
            self.assertIsNone(contribution_div_new)

        _test_procedure("contribution_a15b", delta0=0)
        _test_procedure("contribution_a2b1a1b", delta0=1)

    def test_g100__modal_behavior(self):
        # self.headless = False
        b1 = self.new_browser()

        # testuser_2 -> role b
        self.perform_login(browser=b1, username="testuser_2")
        b1.visit(f"{self.live_server_url}{reverse('test_show_debate')}")

        modal_div_id = "modal-dialog"
        modal_div = b1.find_by_id(modal_div_id)
        self.assertFalse(get_js_visibility_for_id(b1, modal_div_id))
        contribution_key1 = "contribution_a15b"
        contribution_key2 = "contribution_a2b1a1b"
        contribution_div1 = b1.find_by_id(contribution_key1)[0]
        contribution_div2 = b1.find_by_id(contribution_key2)[0]

        trigger_click_event(b1, f"edit_btn_{contribution_key1}")
        self.assertFalse(get_js_visibility_for_id(b1, modal_div_id))

        trigger_click_event(b1, f"edit_btn_{contribution_key2}")
        self.assertFalse(get_js_visibility_for_id(b1, modal_div_id))

        # now type something in the textarea, then press other edit button
        ta2 = contribution_div2.find_by_tag("textarea")[0]
        ta2.type("abc")
        trigger_click_event(b1, f"edit_btn_{contribution_key1}")
        self.assertTrue(get_js_visibility_for_id(b1, modal_div_id))
        trigger_click_event(b1, f"modal-dialog-cancel-button")
        self.assertFalse(get_js_visibility_for_id(b1, modal_div_id))

        # the textarea should not have changed
        res1 = self.fast_get(b1, id_str=contribution_key1, class_str="custom-textarea")
        res2 = self.fast_get(b1, id_str=contribution_key2, class_str="custom-textarea")
        self.assertIsNone(res1)
        self.assertIsNotNone(res2)

        # now do it again but this time clicking "Proceed" (OK)
        trigger_click_event(b1, f"edit_btn_{contribution_key1}")
        self.assertTrue(get_js_visibility_for_id(b1, modal_div_id))
        trigger_click_event(b1, f"modal-dialog-ok-button")
        self.assertFalse(get_js_visibility_for_id(b1, modal_div_id))

        # textarea should have changed
        res1 = self.fast_get(b1, id_str=contribution_key1, class_str="custom-textarea")
        res2 = self.fast_get(b1, id_str=contribution_key2, class_str="custom-textarea")
        self.assertIsNone(res2)
        self.assertIsNotNone(res1)

        # edit textarea 1 then test all the other relevant buttons
        contribution_div1.find_by_tag("textarea")[0].type("abc")

        # both commit buttons
        trigger_click_event(b1, f"commit_btn_{contribution_key1}")
        self.assertTrue(get_js_visibility_for_id(b1, modal_div_id))
        trigger_click_event(b1, f"modal-dialog-cancel-button")

        trigger_click_event(b1, f"commit_btn_{contribution_key2}")
        self.assertTrue(get_js_visibility_for_id(b1, modal_div_id))
        trigger_click_event(b1, f"modal-dialog-cancel-button")

        # both delete buttons
        trigger_click_event(b1, f"delete_btn_{contribution_key1}")
        self.assertTrue(get_js_visibility_for_id(b1, modal_div_id))
        trigger_click_event(b1, f"modal-dialog-cancel-button")

        trigger_click_event(b1, f"delete_btn_{contribution_key2}")
        self.assertTrue(get_js_visibility_for_id(b1, modal_div_id))
        trigger_click_event(b1, f"modal-dialog-cancel-button")

        # cancel button of this textarea
        trigger_click_event(b1, f"cancel_btn_{contribution_key1}")
        self.assertTrue(get_js_visibility_for_id(b1, modal_div_id))
        trigger_click_event(b1, f"modal-dialog-cancel-button")

        # commit-all-button
        trigger_click_event(b1, f"btn_commit_all_ctbs")
        self.assertTrue(get_js_visibility_for_id(b1, modal_div_id))
        trigger_click_event(b1, f"modal-dialog-cancel-button")

    def test_g110__folding_buttons(self):
        # self.headless = False
        b1 = self.new_browser()

        # this special contribution would make testing harder here
        models.Contribution.objects.filter(contribution_key="a2b1a1b").delete()

        # testuser_2 -> role b
        self.perform_login(browser=b1, username="testuser_2")
        b1.visit(f"{self.live_server_url}{reverse('test_show_debate')}")
        num_answers = get_parsed_element_by_id("data-num_answers", browser=b1)
        self.assertEqual(num_answers, 6 + N_CTB_IN_FIXTURES - 1)

        self.assertEqual(b1.evaluate_script("currentLevel"), 0)
        self.assertFalse(get_js_visibility_for_id(b1, "contribution_a2b"))
        self.assertFalse(get_js_visibility_for_id(b1, "contribution_a4b"))
        self.assertFalse(get_js_visibility_for_id(b1, "contribution_a6b"))
        self.assertFalse(get_js_visibility_for_id(b1, "contribution_a7b"))

        # this is faster than finding the elements and calling .click()
        trigger_click_event(b1, "btn_show_level")
        self.assertEqual(b1.evaluate_script("currentLevel"), 1)
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a2b"))
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a4b"))
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a6b"))
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a7b"))

        trigger_click_event(b1, "btn_hide_level")
        self.assertEqual(b1.evaluate_script("currentLevel"), 0)
        self.assertFalse(get_js_visibility_for_id(b1, "contribution_a2b"))
        self.assertFalse(get_js_visibility_for_id(b1, "contribution_a4b"))
        self.assertFalse(get_js_visibility_for_id(b1, "contribution_a6b"))
        self.assertFalse(get_js_visibility_for_id(b1, "contribution_a7b"))

        trigger_click_event(b1, "btn_show_level")
        trigger_click_event(b1, "btn_show_level")
        trigger_click_event(b1, "btn_show_level")
        self.assertEqual(b1.evaluate_script("currentLevel"), 3)
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a2b"))  # level 1
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a2b1a"))  # level 2
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a2b1a3b"))  # level 3

        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a4b"))
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a6b"))
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a7b"))

        trigger_click_event(b1, "btn_hide_level")
        self.assertEqual(b1.evaluate_script("currentLevel"), 2)
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a2b"))  # level 1
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a2b1a"))  # level 2
        self.assertFalse(get_js_visibility_for_id(b1, "contribution_a2b1a3b"))  # level 3

        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a4b"))
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a6b"))
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a7b"))

        trigger_click_event(b1, "btn_show_level")
        self.assertEqual(b1.evaluate_script("currentLevel"), 3)
        trigger_click_event(b1, "btn_show_level")
        self.assertEqual(b1.evaluate_script("currentLevel"), 3)
        trigger_click_event(b1, "btn_hide_level")
        trigger_click_event(b1, "btn_hide_level")
        trigger_click_event(b1, "btn_hide_level")
        self.assertEqual(b1.evaluate_script("currentLevel"), 0)

        self.assertFalse(get_js_visibility_for_id(b1, "contribution_a15b"))
        trigger_click_event(b1, "btn_show_all_ctbs")
        self.assertTrue(get_js_visibility_for_id(b1, "contribution_a15b"))

    def _g120__common(self):
        # self.headless = False
        res = Container()
        res.b1 = self.new_browser()
        res.b2 = self.new_browser()

        # testuser_1 -> role a
        self.perform_login(browser=res.b1, username="testuser_1")
        res.b1.visit(f"{self.live_server_url}{reverse('new_debate')}")

        with open(fdmd.fixtures.txt1_md_fpath) as fp:
            res.content = fp.read()

        body_ta = res.b1.find_by_id("new-debate-body-ta")[0]
        body_ta.type(res.content)

        # no new contribution yet
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES)
        trigger_click_event(res.b1, id="new-debate-submit-btn")
        # one new contribution now
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES + 1)

        api_data_str = get_parsed_element_by_id(id="data-api_data", browser=res.b1)
        res.api_data = json.loads(api_data_str)  # api_data_str is a json str inside a json str

        return res

    def test_g120__new_debate_edit_and_delete(self):
        c = self._g120__common()  # this creates a new a-contribution in the database

        b1, b2 = c.b1, c.b2

        new_url = b1.url
        self.assertIn(reverse("show_debate", kwargs={"debate_key": c.api_data["debate_key"]}), new_url)

        # other users cannot yet see the new debate
        self.perform_login(browser=b2, username="testuser_2")
        b2.visit(new_url)

        status = get_parsed_element_by_id(id="data-server_status_code", browser=b2)
        self.assertEqual(status, 404)

        # test edit and submit
        trigger_click_event(b1, id="edit_btn_contribution_a")

        new_content = f"# Updated content \n\n some new words \n\n{c.content}"
        body_ta = b1.find_by_id("ta_contribution_a")[0]
        body_ta.clear()
        body_ta.type(new_content)
        trigger_click_event(b1, id="submit_btn_contribution_a")
        expected_content = '<h1>\n  <span class="segment" id="a1">\n   Updated content\n  </span>\n </h1>'
        self.assertIn(expected_content, b1.html)

        # now type again and test modal dialog

        trigger_click_event(b1, id="edit_btn_contribution_a")
        body_ta = b1.find_by_id("ta_contribution_a")[0]

        appended_text1 = "\n\nsome words at the end"
        body_ta.type(appended_text1)

        modal_div_id = "modal-dialog"
        self.assertFalse(get_js_visibility_for_id(b1, modal_div_id))
        trigger_click_event(b1, id="edit_btn_contribution_a")
        self.assertTrue(get_js_visibility_for_id(b1, modal_div_id))
        trigger_click_event(b1, f"modal-dialog-cancel-button")
        self.assertFalse(get_js_visibility_for_id(b1, modal_div_id))
        self.assertTrue(body_ta.value.endswith(appended_text1))

        appended_text2 = "\n\nmore stuff for finishing"
        body_ta.type(appended_text2)
        self.assertTrue(body_ta.value.endswith(appended_text2))
        trigger_click_event(b1, id="edit_btn_contribution_a")
        self.assertTrue(get_js_visibility_for_id(b1, modal_div_id))
        trigger_click_event(b1, id="modal-dialog-ok-button")

        # appended_text2 has vanished because we clicked on edit again
        body_ta = b1.find_by_id("ta_contribution_a")[0]
        original_end_text = "Ipsum modi modi quaerat."
        self.assertTrue(body_ta.value.endswith(original_end_text))

        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES + 1)
        self.assertEqual(len(models.Debate.objects.all()), N_DEBATES_IN_FIXTURES + 1)

        trigger_click_event(b1, id="delete_btn_contribution_a")

        # it also worked with 0.01 -> 0.02 is with some safety margin
        time.sleep(0.02)
        self.assertEqual(len(get_js_error_list(b1)), 0)

        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES)
        self.assertEqual(len(models.Debate.objects.all()), N_DEBATES_IN_FIXTURES)

    def test_g121__new_debate_commit(self):
        # self.headless = False
        c = self._g120__common()  # this creates a new a-contribution in the database
        b1, b2 = c.b1, c.b2

        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES + 1)
        self.assertEqual(len(models.Debate.objects.all()), N_DEBATES_IN_FIXTURES + 1)

        self.dirs_to_remove.append(pjoin(REPO_HOST_DIR, c.api_data["debate_key"]))
        trigger_click_event(b1, id="commit_btn_contribution_a")
        new_url = b1.url

        # note: the debate_key somehow depends on which tests had been run before -> no hardcoding
        self.assertIn(reverse("show_debate", kwargs={"debate_key": c.api_data["debate_key"]}), new_url)

        # backend takes some time (0.1s has been too low for some runs -> 0.3s should suffice)
        time.sleep(0.3)
        self.assertEqual(len(get_js_error_list(b1)), 0)
        status_b1 = get_parsed_element_by_id(id="data-server_status_code", browser=b1)
        self.assertEqual(status_b1, 200)

        # other users cannot yet see the new debate
        self.perform_login(browser=b2, username="testuser_2")
        b2.visit(new_url)
        status_b2 = get_parsed_element_by_id(id="data-server_status_code", browser=b2)

        # now the page should be visible also for other users
        self.assertEqual(status_b2, 200)

        user_b = get_parsed_element_by_id(id="data-user_b", browser=b2)
        self.assertEqual(user_b, "__undefined__")

        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES)
        self.assertEqual(len(models.Debate.objects.all()), N_DEBATES_IN_FIXTURES + 1)

        # testuser_1 (in browser b1) should not be able to open answer forms
        trigger_click_event(b1, id="a3")
        self.assertEqual(len(b1.evaluate_script(self.js_segment_contribution_forms)), 0)

        trigger_click_event(b1, id="a4")
        self.assertEqual(len(b1.evaluate_script(self.js_segment_contribution_forms)), 0)

        # testuser_2 (in browser b2) should be able to open answer forms
        trigger_click_event(b2, id="a3")
        self.assertEqual(len(b2.evaluate_script(self.js_segment_contribution_forms)), 1)

        trigger_click_event(b2, id="a4")
        self.assertEqual(len(b2.evaluate_script(self.js_segment_contribution_forms)), 1)

        # compose an answer:
        ta = b2.find_by_tag("textarea")[0]
        ta.type("This is an answer by testuser_2.")

        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES)

        trigger_click_event(b2, f"submit_btn_contribution_a4b")
        time.sleep(0.3)
        self.assertEqual(get_parsed_element_by_id(id="data-server_status_code", browser=b2), 200)

        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES + 1)
        self.assertEqual(get_parsed_element_by_id("data-num_db_ctbs", browser=b2), 1)
        self.assertEqual(get_parsed_element_by_id("data-num_answers", browser=b2), 1)

        trigger_click_event(b2, f"commit_btn_contribution_a4b")
        time.sleep(0.3)
        self.assertEqual(get_parsed_element_by_id(id="data-server_status_code", browser=b2), 200)

        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES)
        self.assertEqual(get_parsed_element_by_id("data-num_db_ctbs", browser=b2), 0)
        self.assertEqual(get_parsed_element_by_id("data-num_answers", browser=b2), 1)


# #################################################################################################

# auxiliary functions:

# #################################################################################################


def get_js_visibility_for_id(browser: BaseWebDriver, id: str):
    """
    Fast visibility check based on Java Script.
    """
    return browser.evaluate_script(f"document.getElementById('{id}').checkVisibility()")


def send_key_to_browser(browser, key, n=1):
    actions = ActionChains(browser.driver)
    for i in range(n):
        actions.send_keys(key)
    actions.perform()


def trigger_click_event(splinter_browser: BaseWebDriver, id: str):
    """
    Motivation: prevent (strange) click problems in headless mode
    """

    script = f'document.getElementById("{id}").click()'
    splinter_browser.execute_script(script)


def trigger_mouseover_event(splinter_browser: BaseWebDriver, id: str):
    """
    Motivation: prevent (strange) mouseover problems in headless mode
    """
    element = splinter_browser.find_by_id(id)[0]
    script = "var event = new MouseEvent('mouseover', {'bubbles': true, 'cancelable': true}); arguments[0].dispatchEvent(event);"
    splinter_browser.execute_script(script, element._element)


def get_js_error_list(browser):
    logs = browser.driver.get_log("browser")
    js_errors = [log for log in logs if log["level"] == "SEVERE"]
    return js_errors
