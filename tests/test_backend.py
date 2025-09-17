import os
import json
import time
from textwrap import dedent as twdd
from datetime import datetime, timedelta, timezone

from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.conf import settings
from django.contrib import auth

from bs4 import BeautifulSoup, element as bs24_element
from packaging.version import Version

from ipydex import IPS
import fair_debate_md as fdmd
from base import models, utils

from .utils import (
    logger,
    RepoResetMixin,
    FollowRedirectMixin,
    Container,
    generate_post_data_for_form,
    get_parsed_element_by_id,
    get_form_base_data_from_html_template_host,
    N_CTB_IN_FIXTURES,
    N_DEBATES_IN_FIXTURES,
    N_USERS_IN_FIXTURES,
    N_COMMITS_TEST_REPO,
    REPO_HOST_DIR,  # note: this is adapted for unittests
)

pjoin = os.path.join


class TestCore1(RepoResetMixin, FollowRedirectMixin, TestCase):
    fixtures = ["tests/testdata/fixtures01.json"]

    @classmethod
    def setUpClass(cls):
        # this is necessary to handle the fixtures
        super().setUpClass()
        logger.info(f"start of TestClass `{cls}`")

    @classmethod
    def tearDownClass(cls):
        logger.info(f"end of TestClass `{cls}`")

    def setUp(self):
        self.set_up()

    def tearDown(self):
        self.tear_down()

    def post_to_view(self, viewname, follow_redirect=None, **kwargs):

        response = self.client.get(reverse(viewname, kwargs=kwargs.get("view_kwargs", {})))
        self.assertEqual(response.status_code, 200)

        spec_values = kwargs.get("spec_values", {})

        post_data, action_url = generate_post_data_for_form(response, spec_values=spec_values)

        response = self.client.post(action_url, post_data)

        if follow_redirect:
            self.assertEqual(response.status_code, 302)
            new_url = response["Location"]
            response = self.client.get(new_url)
            response.url = new_url

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
        self.assertGreaterEqual(Version(fdmd.__version__), Version("0.4.5"))

    def test_010__index(self):
        response = self.client.get(reverse("landing_page"))
        self.assertEqual(response.status_code, 200)
        utd = get_parsed_element_by_id(id="data-utd_page_type", res=response)
        self.assertEqual(utd, "utd_landing_page")

    def test_020__error(self):
        response = self.client.get(reverse("error_page"))
        self.assertEqual(response.status_code, 500)
        utd = get_parsed_element_by_id(id="data-utd_page_type", res=response)
        self.assertEqual(utd, "utd_assertionerror")
        self.assertIn(b"intentionally raised assertion error", response.content)

        # provoke 404
        response = self.client.get("/does/not/exist")

        # this comment is inserted by the error handler (-> no easy transformation to utd possible)
        self.assertIn(b"utc_404_error", response.content)
        self.assertEqual(response.status_code, 404)

    def test_030__new_debate_change_and_delete(self):
        # settings.CATCH_EXCEPTIONS = False

        self.perform_login("testuser_1")
        response = self.client.get(reverse("new_debate"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(models.Debate.objects.all()), N_DEBATES_IN_FIXTURES)
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES)

        utd = get_parsed_element_by_id(id="data-utd_page_type", res=response)
        self.assertEqual(utd, "utd_new_debate")

        self.assertNotIn(b"utc_segmented_html", response.content)

        with open(fdmd.fixtures.txt1_md_fpath) as fp:
            content = fp.read()

        response = self.post_to_view(
            viewname="new_debate",
            spec_values={"body": content, "debate_slug": "test_slug1"},
            follow_redirect=True,
        )
        self.assertEqual(len(models.Debate.objects.all()), N_DEBATES_IN_FIXTURES + 1)
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES + 1)

        # now the client should be redirected show_debate for preview
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, "html.parser")
        bottom_toolbar = soup.find(id="bottom_toolbar")
        self.assertIsNone(bottom_toolbar)

        # this was set by post_to_view
        new_url = response.url

        api_data = json.loads(get_parsed_element_by_id(id="data-api_data", res=response))
        self.assertEqual(new_url, reverse("show_debate", kwargs={"debate_key": api_data["debate_key"]}))

        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)

        num_db_ctbs = get_parsed_element_by_id("data-num_db_ctbs", res=response)
        self.assertEqual(num_db_ctbs, 1)

        _, csrf_token = get_form_base_data_from_html_template_host(response.content)

        self.assertNotIn(b"Updated content", response.content)

        code_block = "```this\nis\na\n   multiline\n   code\nblock```"
        post_data = {
            "csrfmiddlewaretoken": csrf_token,
            "reference_segment": "root_segment",
            "debate_key": api_data["debate_key"],
            "body": f"# Updated content \n\n some new words \n\n {content}\n{code_block}".replace("\n", "\r\n"),
        }

        response = response = self.post_and_follow_redirect(new_url, post_data)
        self.assertEqual(response.status_code, 200)
        expected_content = b'<h1>\n  <span class="segment" id="a1">\n   Updated content\n  </span>\n </h1>'
        self.assertIn(expected_content, response.content)

        # other user should not see anything before committing
        self.perform_login("testuser_2")

        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 404)

        # now test deletion
        self.perform_login("testuser_1")

        response = self.client.get(new_url)
        api_data_str = get_parsed_element_by_id(id="data-api_data", res=response)
        api_data = json.loads(api_data_str)  # api_data_str is a json str inside a json str
        _, csrf_token = get_form_base_data_from_html_template_host(response.content)

        post_data = {
            "csrfmiddlewaretoken": csrf_token,
            "debate_key": api_data["debate_key"],
            "contribution_key": "a",
        }

        # test deletion of contribution and the whole debate
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES + 1)
        self.assertEqual(len(models.Debate.objects.all()), N_DEBATES_IN_FIXTURES + 1)
        response = self.post_and_follow_redirect(action_url=api_data["delete_url"], post_data=post_data)
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES)
        self.assertEqual(len(models.Debate.objects.all()), N_DEBATES_IN_FIXTURES)

        # after debate-deletion we redirect to landing page
        self.assertEqual(response.status_code, 200)
        utd = get_parsed_element_by_id(id="data-utd_page_type", res=response)
        self.assertEqual(utd, "utd_landing_page")

    def test_030_i25__slug_with_special_chars(self):
        settings.CATCH_EXCEPTIONS = False
        self.perform_login("testuser_1")

        with open(fdmd.fixtures.txt1_md_fpath) as fp:
            content = fp.read()

        response = self.post_to_view(
            viewname="new_debate",
            spec_values={"body": content, "debate_slug": "Slug with special→Chars: ¡…¿łöſµŋéÑ? !"},
            follow_redirect=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(models.Debate.objects.all()), N_DEBATES_IN_FIXTURES + 1)

    def test_035__new_debate_commit(self):
        # settings.CATCH_EXCEPTIONS = False

        self.perform_login("testuser_1")
        # response = self.client.get(reverse("new_debate"))
        with open(fdmd.fixtures.txt1_md_fpath) as fp:
            content = fp.read()

        # create new contribution in database mode
        response = self.post_to_view(
            viewname="new_debate",
            spec_values={"body": content, "debate_slug": "test_slug1"},
            follow_redirect=True,
        )

        # new a-contribution was submitted to database but not yet committed
        # (indirectly) check that it is not shown on landing page for for anonymous user
        n1 = len(models.Debate.get_all())
        n2 = len(models.Debate.get_all(exclude_uncommitted=False))
        self.assertEqual(n2, n1 + 1)

        # gather necessary data to simulate commit-button-press
        api_data_str = get_parsed_element_by_id(id="data-api_data", res=response)
        api_data = json.loads(api_data_str)  # api_data_str is a json str inside a json str
        _, csrf_token = get_form_base_data_from_html_template_host(response.content)

        post_data = {
            "csrfmiddlewaretoken": csrf_token,
            "debate_key": api_data["debate_key"],
            "contribution_key": "a",
        }

        # check data before commit
        self.assertEqual(len(models.Debate.objects.all()), N_DEBATES_IN_FIXTURES + 1)
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES + 1)

        # simulate commit button press

        target_dir = pjoin(REPO_HOST_DIR, api_data["debate_key"])
        self.dirs_to_remove.append(target_dir)
        response = self.post_and_follow_redirect(action_url=api_data["commit_url"], post_data=post_data)

        assert "testdata" in REPO_HOST_DIR

        # check data changed after commit:
        # db-contribution should be gone
        self.assertEqual(len(models.Debate.objects.all()), N_DEBATES_IN_FIXTURES + 1)
        # debate should still be there
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES)

        fpath = pjoin(target_dir, "a", "a.md")
        with open(fpath) as fp:
            md_content = fp.read()

        self.assertNotIn("::code_placeholder_", md_content)
        self.assertIn("```This\nis\na\ncode\n\nblock```", md_content)

        # now add reply (db_ctb) by testuser_2
        debate_key = api_data["debate_key"]
        self.perform_login("testuser_2")
        new_debate_url = reverse("show_debate", kwargs={"debate_key": debate_key})
        response = self.client.get(new_debate_url)

        self.assertEqual(get_parsed_element_by_id("data-num_db_ctbs", res=response), 0)
        self.assertEqual(get_parsed_element_by_id("data-num_answers", res=response), 0)

        action_url, csrf_token = get_form_base_data_from_html_template_host(response.content)

        post_data_a3 = {
            "csrfmiddlewaretoken": csrf_token,
            # hard coded data
            "reference_segment": "a3",
            "debate_key": debate_key,
            "body": (
                "This is a level 1 **answer** from a unittest."
            ),
        }
        response = self.post_and_follow_redirect(action_url, post_data_a3)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(get_parsed_element_by_id("data-num_db_ctbs", res=response), 1)
        self.assertEqual(get_parsed_element_by_id("data-num_answers", res=response), 1)

        # now also commit the new answer
        action_url_commit = reverse("commit_contribution")

        post_data_commit = {
            "csrfmiddlewaretoken": csrf_token,
            # hard coded data
            "debate_key": debate_key,
            "contribution_key": "a3b",
        }

        response = self.post_and_follow_redirect(action_url_commit, post_data_commit)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(get_parsed_element_by_id("data-num_db_ctbs", res=response), 0)
        self.assertEqual(get_parsed_element_by_id("data-num_answers", res=response), 1)

    def test_036__markdown_rendering_of_backticks(self):
        self.perform_login("testuser_1")
        # response = self.client.get(reverse("new_debate"))

        # create new contribution in database mode

        content = (
            "This is a level 0 **post** from a unittest"
            "\n\n```\nincluding\n#triple\nbackticks```\n."
        ),
        response = self.post_to_view(
            viewname="new_debate",
            spec_values={"body": content, "debate_slug": "test_slug1"},
            follow_redirect=True,
        )

        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        span_code_element = soup.find(id="a2")

        self.assertEqual(span_code_element.name, "span")
        code_element = span_code_element.find("code")
        self.assertEqual(code_element.name, "code")
        self.assertEqual(code_element.text, "\nincluding\n#triple\nbackticks")

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
        self.assertEqual(new_url, reverse("landing_page"))
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)

        self.perform_logout()

        # test if redirect with ?next=... works
        response = self.perform_login(next_url=reverse("test_show_debate"))
        self.assertEqual(response.status_code, 302)
        new_url = response["Location"]
        self.assertEqual(new_url, reverse("test_show_debate"))

    def test_051__h3_answer_rendering(self):
        """
        test for issue (#i3): Answers to h1, h2, h3 tags should be rendered
        outside of those tags.
        """

        # login with role b to see the relevant uncommitted contribution
        response = self.perform_login(username="testuser_2")

        response = self.client.get(reverse("test_show_debate"))

        # if this test fails with status_code 404, then probably the test data is missing
        # see README.md
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        segment_span = soup.find(id="a15")
        contribution_div = soup.find(id="contribution_a15b")
        self.assertEqual(segment_span.parent.name, "h3")

        # currently failing (not yet implemented)
        self.assertNotEqual(contribution_div.parent.name, "h3")

    def test_052__debate_listing_for_landing_page(self):

        user1 = models.DebateUser.objects.get(username="testuser_1")
        user2 = models.DebateUser.objects.get(username="testuser_2")
        user3 = models.DebateUser.objects.get(username="testuser_3")

        debates_u1 = models.Debate.get_for_user(user1)
        debates_u2 = models.Debate.get_for_user(user2)
        debates_u3 = models.Debate.get_for_user(user3)

        self.assertEqual(len(debates_u1), 4)
        self.assertEqual(len(debates_u2), 3)
        self.assertEqual(len(debates_u3), 1)

        # ensure sorting

        debates_all_3 = models.Debate.get_all(limit=3)
        debates_all_4 = models.Debate.get_all(limit=4)

        oldest_debate: models.Debate = debates_all_4[3]

        deb: models.Debate
        for deb in debates_all_3:
            self.assertLess(oldest_debate.update_date, deb.update_date)

    def test_053__signup(self):
        users = models.DebateUser.objects.all()
        self.assertEqual(len(users), N_USERS_IN_FIXTURES)

        res = self.client.get(reverse("signup"))
        password = "cho8/Uk8l+5fh"  #
        post_data, action_url = generate_post_data_for_form(
            res, spec_values={"username": "testuser_tmp", "password1": password, "password2": password}
        )

        settings.CATCH_EXCEPTIONS = False
        res2 = self.post_and_follow_redirect(action_url, post_data)

        self.assertEqual(res2.status_code, 200)
        users = models.DebateUser.objects.all()
        self.assertEqual(len(users), N_USERS_IN_FIXTURES + 1)

        # now check that exception is thrown for too simple password
        post_data, action_url = generate_post_data_for_form(
            res, spec_values={"username": "testuser_tmp2", "password1": "12345678", "password2": "12345678"}
        )

        CATCH_EXCEPTIONS = settings.CATCH_EXCEPTIONS
        settings.CATCH_EXCEPTIONS = False
        with self.assertRaises(utils.FormValidationError):
            res = self.post_and_follow_redirect(action_url, post_data)
        settings.CATCH_EXCEPTIONS = CATCH_EXCEPTIONS  # restore previous behavior

        settings.CATCH_EXCEPTIONS = True
        res = self.client.post(action_url, post_data)
        self.assertEqual(get_parsed_element_by_id(id="data-server_status_code", res=res), 500)
        self.assertEqual(
            get_parsed_element_by_id(id="data-utd_page_type", res=res), "utd_formvalidationerror"
        )

    def _06x__common(self) -> Container:

        # ensure file system based test data exists:

        res = Container()
        res.TEST_REPO1_PATH = os.path.join(settings.REPO_HOST_DIR, fdmd.TEST_DEBATE_KEY, ".git")
        if not os.path.isdir(res.TEST_REPO1_PATH):
            raise FileNotFoundError(res.TEST_REPO1_PATH)

        # settings.CATCH_EXCEPTIONS = False

        url = reverse("test_show_debate")
        res.response = self.client.get(url)

        # if this fails, probably ./content_repos is not initialized
        # solution: `fdmd unpack-repos ./content_repos``
        self.assertEqual(res.response.status_code, 200)

        res.action_url, res.csrf_token = get_form_base_data_from_html_template_host(res.response.content)

        res.post_data_a3 = {
            "csrfmiddlewaretoken": res.csrf_token,
            # hard coded data
            "reference_segment": "a3",
            "debate_key": fdmd.TEST_DEBATE_KEY,
            "body": "This is a level 1 **answer** from a unittest.",
        }

        res.post_data_a3_updated = res.post_data_a3.copy()
        res.post_data_a3_updated.update(
            {
                "body": "This is an updated level 1 **answer** from a unittest.",
            }
        )

        res.post_data_a4b4 = res.post_data_a3.copy()
        res.post_data_a4b4.update(
            {
                "reference_segment": "a4b4",
                "body": "This is a level 2 *answer* from a unittest.",
            }
        )

        res.debate_obj1 = models.Debate.objects.get(debate_key=fdmd.TEST_DEBATE_KEY)

        return res

    def test_060__add_contribution_level1_without_login(self):
        c = self._06x__common()

        deepest_level = get_parsed_element_by_id("data-deepest_level", res=c.response)
        self.assertEqual(deepest_level, 3)

        response = self.client.post(c.action_url, c.post_data_a3)
        self.assertEqual(response.status_code, 302)
        new_url = response["Location"]
        self.assertTrue(new_url.startswith("/login"))
        response = self.client.get(new_url)

    def test_061__add_contribution_level1(self):
        # settings.CATCH_EXCEPTIONS = False
        c = self._06x__common()

        # first wrong user (testuser_1, role: a)
        response = self.perform_login(username="testuser_1")
        response = self.client.post(c.action_url, c.post_data_a3)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"utc_contribution_with_wrong_mode_not_allowed_for_user", response.content)

        response = self.client.get(reverse("test_show_debate"))
        user_role = get_parsed_element_by_id(id="data-user_role", res=response)
        self.assertEqual(user_role, "a")

        # second wrong user (testuser_3, role: None)
        response = self.perform_login(username="testuser_3", logout_first=True)
        response = self.client.post(c.action_url, c.post_data_a3)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"utc_no_contribution_allowed_for_user", response.content)

        response = self.client.get(reverse("test_show_debate"))
        user_role = get_parsed_element_by_id(id="data-user_role", res=response)
        self.assertEqual(user_role, None)

        # correct user (testuser_2, role: b)
        self.perform_login(username="testuser_2", logout_first=True)

        response = self.client.get(reverse("test_show_debate"))
        user_role = get_parsed_element_by_id(id="data-user_role", res=response)
        self.assertEqual(user_role, "b")

        self.assertEqual(len(c.debate_obj1.contribution_set.all()), N_CTB_IN_FIXTURES)

        response = self.post_and_follow_redirect(c.action_url, c.post_data_a3)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(c.debate_obj1.contribution_set.all()), N_CTB_IN_FIXTURES + 1)
        soup = BeautifulSoup(response.content, "html.parser")
        contribution_div = soup.find(id="contribution_a3b")
        self.assertIsNotNone(contribution_div)
        self.assertIn("db_ctb", contribution_div.attrs["class"])
        segment_span = contribution_div.find(id="a3b1")
        self.assertIsNotNone(segment_span)

        expected_res = "This is a level 1\n     <strong>\n      answer\n     </strong>\n     from a unittest."
        res = "".join(map(str, segment_span.contents)).strip()
        self.assertEqual(res, expected_res)

        # we are still testuser_2
        # send data for that segment key again with different body (update post)
        response = self.post_and_follow_redirect(c.action_url, c.post_data_a3_updated)

        # ensure that no additional object is created
        self.assertEqual(len(c.debate_obj1.contribution_set.all()), N_CTB_IN_FIXTURES + 1)
        expected_res = (
            "This is an updated level 1\n     <strong>\n      answer\n     </strong>\n     from a unittest."
        )

        soup = BeautifulSoup(response.content, "html.parser")
        segment_span = soup.find(id="a3b1")
        res = "".join(map(str, segment_span.contents)).strip()
        self.assertEqual(res, expected_res)

    def test_062__add_contribution__level2(self):
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
        response = self.post_and_follow_redirect(c.action_url, c.post_data_a4b4)
        self.assertEqual(len(c.debate_obj1.contribution_set.all()), N_CTB_IN_FIXTURES + 1)
        expected_res = (
            "This is a level 2\n        <em>\n         answer\n        </em>\n        from a unittest."
        )

        soup = BeautifulSoup(response.content, "html.parser")
        segment_span = soup.find(id="a4b4a1")
        res = "".join(map(str, segment_span.contents)).strip()
        self.assertEqual(res, expected_res)

    def test_063__add_empty_answer(self):
        c = self._06x__common()
        self.perform_login(username="testuser_2")

        c.post_data_a3.update(
            {
                "body": "",
            }
        )
        response = self.client.post(c.action_url, c.post_data_a3)
        self.assertEqual(response.status_code, 500)
        utd = get_parsed_element_by_id(id="data-utd_page_type", res=response)
        self.assertEqual(utd, "utd_usageerror")

    def _07x__common(self):
        res = Container()
        res06x = self._06x__common()
        res.csrf_token = res06x.csrf_token

        res.repo_dir = os.path.join(settings.REPO_HOST_DIR, fdmd.TEST_DEBATE_KEY)

        res.post_data_a15b = {
            "csrfmiddlewaretoken": res.csrf_token,
            # hard coded data
            "debate_key": fdmd.TEST_DEBATE_KEY,
            "contribution_key": "a15b",
        }

        res.fpaths_a15b = [os.path.join(res.repo_dir, "b", f'{res.post_data_a15b["contribution_key"]}.md')]

        res.post_data_a2b1a1b = res.post_data_a15b.copy()
        res.post_data_a2b1a1b.update({"contribution_key": "a2b1a1b"})
        res.action_url_single = reverse("commit_contribution")
        res.action_url_all = reverse("commit_all_contributions")

        res.post_data_all = res.post_data_a15b.copy()
        res.post_data_all.pop("contribution_key")
        res.fpaths_all = [
            os.path.join(res.repo_dir, "b", f'{res.post_data_a15b["contribution_key"]}.md'),
            os.path.join(res.repo_dir, "b", f'{res.post_data_a2b1a1b["contribution_key"]}.md'),
        ]

        return res

    def test_070__commit_contributions(self):
        c = self._07x__common()

        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES)

        self.perform_login(username="testuser_2")

        repo_dir = os.path.join(settings.REPO_HOST_DIR, fdmd.TEST_DEBATE_KEY)

        for fpath in c.fpaths_a15b:
            self.assertFalse(os.path.exists(fpath))

        nbr_of_commits = fdmd.utils.get_number_of_commits(repo_dir=repo_dir)
        self.mark_repo_for_reset(repo_dir)
        self.assertEqual(nbr_of_commits, N_COMMITS_TEST_REPO)

        debate_obj = models.Debate.objects.get(debate_key="d1-lorem_ipsum")
        n1 = debate_obj.n_committed_contributions

        # now send the post request (commit contribution)
        response = self.client.post(c.action_url_single, c.post_data_a15b)

        debate_obj = models.Debate.objects.get(debate_key="d1-lorem_ipsum")

        # ensure that the debate was updated
        time_diff = datetime.now(tz=timezone.utc) - debate_obj.update_date
        self.assertLess(time_diff, timedelta(seconds=0.3))

        # ensure number of committed contribution has increased
        n2 = debate_obj.n_committed_contributions
        self.assertEqual(n2, n1 + 1)

        self.assertEqual(response.status_code, 302)
        target_url = response["Location"]
        self.assertEqual(target_url, reverse("test_show_debate"))

        for fpath in c.fpaths_a15b:
            self.assertTrue(os.path.exists(fpath))

        nbr_of_commits = fdmd.utils.get_number_of_commits(repo_dir=repo_dir)
        self.assertEqual(nbr_of_commits, N_COMMITS_TEST_REPO + 1)

        # check that one contribution in db is gone
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES - 1)

    def test_071__commit_contributions(self):
        c = self._07x__common()
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES)
        self.perform_login(username="testuser_2")

        nbr_of_commits = fdmd.utils.get_number_of_commits(repo_dir=c.repo_dir)
        self.mark_repo_for_reset(c.repo_dir)
        self.assertEqual(nbr_of_commits, N_COMMITS_TEST_REPO)
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES)

        for fpath in c.fpaths_all:
            self.assertFalse(os.path.exists(fpath))

        response = self.client.get(reverse("test_show_debate"))
        ctb_divs = BeautifulSoup(response.content, "html.parser").find_all("div", attrs={"class": "db_ctb"})
        self.assertEqual(len(ctb_divs), 2)
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES)

        debate_obj = models.Debate.objects.get(debate_key="d1-lorem_ipsum")
        n1 = debate_obj.n_committed_contributions

        # trigger the commit of all contributions
        response = self.post_and_follow_redirect(c.action_url_all, c.post_data_all)
        self.assertEqual(response.request["PATH_INFO"], reverse("test_show_debate"))

        # ensure that the debate was updated
        debate_obj = models.Debate.objects.get(debate_key="d1-lorem_ipsum")
        time_diff = datetime.now(tz=timezone.utc) - debate_obj.update_date
        self.assertLess(time_diff, timedelta(seconds=1))

        # ensure number of committed contribution has increased
        n2 = debate_obj.n_committed_contributions
        self.assertEqual(n2, n1 + 2)
        # ensure number of non-committed contribution in db has decreased
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES - 2)

        # now no divs with this class should be in the response
        ctb_divs = BeautifulSoup(response.content, "html.parser").find_all("div", attrs={"class": "db_ctb"})
        self.assertEqual(len(ctb_divs), 0)

        nbr_of_commits = fdmd.utils.get_number_of_commits(repo_dir=c.repo_dir)
        self.assertEqual(nbr_of_commits, N_COMMITS_TEST_REPO + 1)

        for fpath in c.fpaths_all:
            self.assertTrue(os.path.exists(fpath))

        # check that all contributions in db are gone
        self.assertEqual(len(models.Contribution.objects.all()), 0)

    def _08x__common(self):
        res = self._07x__common()
        del res.action_url_single
        del res.action_url_all

        res.action_url_delete = reverse("delete_contribution")
        return res

    def test_080__delete_contribution(self):
        c = self._08x__common()
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES)
        self.perform_login(username="testuser_2")

        # send delete request
        response = self.client.post(c.action_url_delete, c.post_data_a15b)

        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES - 1)
