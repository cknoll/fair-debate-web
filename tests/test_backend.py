import os
import json
import time

from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.conf import settings
from django.contrib import auth

from bs4 import BeautifulSoup, element as bs24_element
from packaging.version import Version

from ipydex import IPS
import fair_debate_md as fdmd
from base import models

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
    N_COMMITS_TEST_REPO
)


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
        self.assertGreaterEqual(Version(fdmd.__version__), Version("0.3.9"))

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

    def test_030__new_debate(self):
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

        # now the preview is available
        response = self.post_to_view(
            viewname="new_debate", spec_values={"body_content": content, "debate_slug": "test_slug1"}
        )
        self.assertEqual(len(models.Debate.objects.all()), N_DEBATES_IN_FIXTURES + 1)

        # not yet implemented
        self.assertEqual(len(models.Contribution.objects.all()), N_CTB_IN_FIXTURES + 1)

        self.assertEqual(response.status_code, 302)
        new_url = response["Location"]
        self.assertEqual(new_url, reverse("show_debate",  kwargs={"debate_key": "d2-test_slug1"}))
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)

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
        soup = BeautifulSoup(response.content, "html.parser")
        segment_span = soup.find(id="a15")
        answer_div = soup.find(id="answer_a15b")
        self.assertEqual(segment_span.parent.name, "h3")

        # currently failing (not yet implemented)
        self.assertNotEqual(answer_div.parent.name, "h3")

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

        deepest_level = get_parsed_element_by_id("data-deepest_level", res=c.response)
        self.assertEqual(deepest_level, 3)

        response = self.client.post(c.action_url, c.post_data_a3)
        self.assertEqual(response.status_code, 302)
        new_url = response["Location"]
        self.assertTrue(new_url.startswith("/login"))
        response = self.client.get(new_url)

    def test_061__add_answer_level1(self):
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
        answer_div = soup.find(id="answer_a3b")
        self.assertIsNotNone(answer_div)
        self.assertIn("db_ctb", answer_div.attrs["class"])
        segment_span = answer_div.find(id="a3b1")
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

        c.post_data_a3.update({"body": "",})
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
            "contribution_key": "a15b"
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
            os.path.join(res.repo_dir, "b", f'{res.post_data_a2b1a1b["contribution_key"]}.md')
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

        # now send the post request
        response = self.client.post(c.action_url_single, c.post_data_a15b)

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

        for fpath in c.fpaths_all:
            self.assertFalse(os.path.exists(fpath))

        response = self.client.get(reverse("test_show_debate"))
        ctb_divs = BeautifulSoup(response.content, "html.parser").find_all("div", attrs={"class":"db_ctb"})
        self.assertEqual(len(ctb_divs), 2)

        response = self.post_and_follow_redirect(c.action_url_all, c.post_data_all)
        self.assertEqual(response.request["PATH_INFO"], reverse("test_show_debate"))

        # now no divs with this class should be in the response
        ctb_divs = BeautifulSoup(response.content, "html.parser").find_all("div", attrs={"class":"db_ctb"})
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
