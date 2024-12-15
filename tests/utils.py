import os
import json
import time
import logging

from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.conf import settings
from django.http.response import HttpResponse
from django.contrib import auth

from bs4 import BeautifulSoup, element as bs24_element
from packaging.version import Version
import git

from splinter import Browser, Config
from splinter.driver.webdriver import BaseWebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

from ipydex import IPS
import fair_debate_md as fdmd
from base import models

pjoin = os.path.join

logger = logging.getLogger("fair-debate")
logger.debug("fair_debate_web.tests.utils loaded")


class Container:
    pass


N_CTB_IN_FIXTURES = 2
N_DEBATES_IN_FIXTURES = 4
N_COMMITS_TEST_REPO = 4

original_REPO_HOST_DIR = settings.REPO_HOST_DIR
REPO_HOST_DIR_rel = original_REPO_HOST_DIR.replace(settings.BASE_DIR, "").lstrip("/")
settings.REPO_HOST_DIR = pjoin(settings.BASE_DIR, "tests", "testdata", REPO_HOST_DIR_rel)
REPO_HOST_DIR = settings.REPO_HOST_DIR
os.makedirs(settings.REPO_HOST_DIR, exist_ok=True)


class RepoResetMixin:
    def set_up(self):
        self.git_reset_id: str = None
        self.git_reset_repo: str = None
        self.dirs_to_remove = []

    def tear_down(self):
        if self.git_reset_id is not None:
            self.reset_git_repo()

        for dirpath in self.dirs_to_remove:
            dirpath = os.path.abspath(dirpath)
            # try to prevent the accidental deletion of important dir
            assert "testdata" in dirpath or "fixtures" in dirpath or "/tmp" in dirpath
            fdmd.utils.tolerant_rmtree(dirpath)

    def mark_repo_for_reset(self, repo_dir: str = None, repo_host_dir: str = None, debate_key: str = None):
        if repo_dir is not None:
            assert repo_host_dir is None
            assert debate_key is None
        else:
            assert debate_key is not None
            if repo_host_dir is None:
                repo_host_dir = settings.REPO_HOST_DIR
            repo_dir = os.path.join(repo_host_dir, debate_key)

        assert os.path.isdir(repo_dir)
        self.git_reset_repo = repo_dir
        repo = git.Repo(self.git_reset_repo)
        self.git_reset_id = repo.refs[0].commit.hexsha

    def reset_git_repo(self):

        repo = git.Repo(self.git_reset_repo)
        repo.head.reset(self.git_reset_id, index=True, working_tree=True)


class FollowRedirectMixin:
    def post_and_follow_redirect(self, action_url: str, post_data: dict) -> HttpResponse:
        response = self.client.post(action_url, post_data)

        # redirect
        self.assertEqual(response.status_code, 302)
        new_url = response["Location"]
        response = self.client.get(new_url)
        return response


# #################################################################################################

# auxiliary functions:

# #################################################################################################


def get_parsed_element_by_id(id: str, res: HttpResponse = None, browser: Browser = None):

    if browser is None:
        assert isinstance(res, HttpResponse)
        # for usage with http response
        soup = BeautifulSoup(res.content, "html.parser")
        element = soup.find(id=id)
        assert element is not None, f'no element with id="{id}" could be found in response.'
        content_str = "".join(element.contents)
    elif res is None:
        assert isinstance(browser, BaseWebDriver)
        # for usage with splinter browser
        element = browser.find_by_id(id)[0]
        content_str = element.html
    return json.loads(content_str)


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


def get_form_base_data_from_html_template_host(response_content: bytes) -> str:
    """
    This function expects that the csrf token is available within a template-tag with a special
    id.

    Motivation: for dynamically created forms it is not possible to generate the post data the usual way.
    This function helps to create it manually.
    """
    soup = BeautifulSoup(response_content, "html.parser")
    # api_data = json.loads(soup.find(id="data-api_data").text)
    action_url = json.loads(soup.find(id="data-action_url").text)
    csrf_token = json.loads(soup.find(id="data-csrf_token").text)

    return action_url, csrf_token
