import os
from django.conf import settings
from django.views import View
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import OperationalError

from .forms import UserCreationForm, LoginForm
from .models import Debate, Contribution, DebateUser


import fair_debate_md as fdmd

from .simple_pages_interface import get_sp, new_sp
from . import simple_pages_content_default as spc
from . import utils

from ipydex import IPS

pjoin = os.path.join


class Container:
    pass


class MainView(View):
    def get(self, request):
        context = {
            # nested dict for easier debugging in the template
            "data": {
                "sp": None,
                "utd_page_type": "utd_landingpage",
            }
        }

        context["data"]["sp"] = get_sp("landing")
        # template = "base/main_simplepage.html"
        template = "base/main_landingpage.html"

        return render(request, template, context)

    def post(self, request, **kwargs):

        raise NotImplementedError


class NewDebateView(View):
    def get(self, request, test=False):
        return self.render_result_from_md(request, body_content_md="")

    def post(self, request, **kwargs):
        body_content = request.POST.get("body_content", "")
        return self.render_result_from_md(request, body_content)

    def render_result_from_md(self, request, body_content_md):

        md_with_keys, segmented_html = fdmd.convert_plain_md_to_segmented_html(body_content_md)
        if body_content_md:
            submit_label = "Submit"
        else:
            submit_label = "Preview"

        context = {
            "data": {
                "utd_page_type": "utd_new_debate",
                "md_with_keys": md_with_keys,
                "segmented_html": segmented_html,
                "submit_label": submit_label,
            }
        }
        template = "base/main_new_debate.html"

        # TODO: maybe redirect here
        return render(request, template, context)


def test_new_debate(request):
    """
    Show the preview (edit) mode with some preloaded fixture data
    This view simplifies interactive testing during development
    """

    with open(fdmd.fixtures.txt1_md_fpath) as fp:
        body_content = fp.read()

    return NewDebateView().render_result_from_md(request, body_content_md=body_content)


class ShowDebateView(View):
    def get(self, request, debate_key=None, test=False):

        if test:
            # Show the display (show) mode with some preloaded fixture data (containing answers)
            # This view simplifies interactive testing during development
            debate_key = fdmd.TEST_DEBATE_KEY

            # TEST_DEBATE_DIR1 = pjoin(fdmd.fixtures.path, "debate1")

        assert debate_key is not None

        ctb_list = self._get_ctb_list_from_db(author=request.user, debate_obj_or_key=fdmd.TEST_DEBATE_KEY)
        ddl = fdmd.load_repo(settings.REPO_HOST_DIR, debate_key, ctb_list=ctb_list)
        # ddl = fdmd.load_dir(TEST_DEBATE_DIR1, ctb_list=ctb_list)
        return self.render_result_from_html(request, body_content_html=ddl.final_html, debate_obj_or_key=ddl.debate_key)

    @method_decorator(login_required(login_url=f"/{settings.LOGIN_URL}"))
    def post(self, request, **kwargs):

        debate_key = request.POST["debate_key"]
        debate_obj = Debate.objects.get(debate_key=debate_key)

        contribution_key = fdmd.get_answer_contribution_key(request.POST["reference_segment"])
        answer_mode = contribution_key[-1]
        assert answer_mode in ("a", "b")

        user_role = debate_obj.get_user_role(request.user)
        if err_page := self._ensure_suitable_user_role(request, user_role, answer_mode):
            return err_page

        self.create_or_update_contribution(request, debate_obj, contribution_key)

        ctb_list = self._get_ctb_list_from_db(author=request.user, debate_obj_or_key=debate_obj)
        ddl: fdmd.DebateDirLoader = fdmd.load_repo(settings.REPO_HOST_DIR, debate_key, ctb_list=ctb_list)

        return self.render_result_from_html(request, body_content_html=ddl.final_html, debate_obj_or_key=ddl.debate_key)

    def create_or_update_contribution(self, request, debate_obj: Debate, contribution_key: str) -> Contribution:
        """
        return updated existing or new Contribution-object
        """

        contribution_obj: Contribution
        if contribution_obj := utils.get_or_none(debate_obj.contribution_set, contribution_key=contribution_key):
            contribution_obj.body = request.POST["body"]
            contribution_obj.save()

        else:
            contribution_obj = Contribution(
                author=request.user,
                debate=debate_obj,
                contribution_key=contribution_key,
                body=request.POST["body"],
            )

        contribution_obj.save()
        return contribution_obj


    def _ensure_suitable_user_role(self, request, user_role, answer_mode):

        if user_role is None:
            msg = (
                f"You ({request.user}) are not allowed to contribute to this debate."
                "<!-- utc_no_contribution_allowed_for_user -->"
            )
            return error_page(request, title="Contribution Error", msg=msg, status=403)

        if answer_mode != user_role:
            msg = (
                f"You ({request.user}) have role {user_role} in this debate but tried to "
                f"contribute with role {answer_mode}. This is not allowed."
                "<!-- utc_contribution_with_wrong_mode_not_allowed_for_user -->"
            )
            return error_page(request, title="Contribution Error", msg=msg, status=403)

    def _get_ctb_list_from_db(self, author: DebateUser, debate_obj_or_key) -> list[fdmd.DBContribution]:

        if not author.is_authenticated:
            return []

        if isinstance(debate_obj_or_key, str):
            debate_obj = Debate.objects.get(debate_key=debate_obj_or_key)
        else:
            debate_obj = debate_obj_or_key
        assert isinstance(debate_obj, Debate)

        ctb_list = []
        ctb_obj: Contribution
        ctb_obj_set = debate_obj.contribution_set.filter(author=author)
        for ctb_obj in ctb_obj_set:
            ctb_list.append(fdmd.DBContribution(ctb_key=ctb_obj.contribution_key, body=ctb_obj.body))

        return ctb_list

    def render_result_from_html(self, request, body_content_html, debate_obj_or_key: Debate|str):

        if isinstance(debate_obj_or_key, str):
            debate_obj = Debate.objects.get(debate_key=debate_obj_or_key)
        else:
            debate_obj = debate_obj_or_key
        assert isinstance(debate_obj, Debate)

        context = {
            "data": {
                "utd_page_type": f"utd_new_debate",
                "segmented_html": body_content_html,
                "debate_title": "untitled debate",
                "debate_key": debate_obj.debate_key,
                "user_role": debate_obj.get_user_role(request.user)
            }
        }
        template = "base/main_show_debate.html"

        # TODO: maybe redirect here
        return render(request, template, context)


def errorpage(request):
    # serve a page via get request to simplify the display of source code in browser

    assert False, "intentionally raised assertion error"


def debugpage(request):
    # serve a page via get request to simplify the display of source code in browser
    msg = f"""
    this is a debug page\n

    {settings.REPO_HOST_DIR=}
    {settings.VERSION=}

    """
    return error_page(request, title="debug page", msg=msg, status=200)


def js_error_page(request):
    """
    This view-function serves to deliberately trigger an javascript error.
    Motivation: check if this error is caught by unittests.
    """

    res = error_page(
        request,
        title="deliberate javascript error (for testing purposes)",
        msg="This page contains a deliberate javascript error (for testing purposes).",
        status=200,
        extra_data={"trigger_js_error": True, "utd_page_type": f"utd_trigger_js_error_page",},
    )

    return res


def error_page(request, title, msg, status=500, extra_data: dict = None):
    sp_type = title.lower().replace(" ", "_")
    sp = new_sp(
        type=sp_type,
        title=title,
        # TODO handle translation (we can not simple use
        # django.utils.translation.gettext here)
        content=msg,
    )

    context = {
        # nested dict for easier debugging in the template
        "data": {
            "sp": sp,
            "main_class": "error_container",
            "utd_page_type": f"utd_{sp_type}",
        }
    }

    if extra_data:
        context["data"].update(extra_data)

    template = "base/main_simplepage.html"

    return render(request, template, context, status=status)


def about_page(request):

    context = {
        # nested dict for easier debugging in the template
        "data": {
            "sp": get_sp("about"),
            # "main_class": "error_container",
            "utd_page_type": f"utd_about_page",
        }
    }

    template = "base/main_simplepage.html"

    return render(request, template, context)


def menu_page(request):
    context = {}
    template = "base/main_menu_page.html"

    return render(request, template, context)


# Source: https://medium.com/@devsumitg/django-auth-user-signup-and-login-7b424dae7fab


# signup page
def user_signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "main_auth_signup.html", {"form": form})


# login page
def user_login(request):
    data = {
        "failed_login_attempt": None,
        "next_url": request.GET.get("next"),  # this allows requests to /login/?next=/show/test
    }

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if next_url := request.POST.get("next_url"):
                    return HttpResponseRedirect(next_url)
                else:
                    return redirect("landingpage")
            else:
                data["failed_login_attempt"] = True
    else:
        form = LoginForm()
    return render(request, "main_auth_login.html", {"form": form, "data": data})


# logout page
def user_logout(request):
    logout(request)
    return redirect("landingpage")


# End of medium source
