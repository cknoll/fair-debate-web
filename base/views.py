import os
import json
from urllib.parse import urlencode
import logging

from django.conf import settings
from django.views import View
from django.http import HttpResponseRedirect, QueryDict
from django.shortcuts import render, redirect
from django.urls import reverse


from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.contrib.auth import authenticate, login, logout
from django.db.models import QuerySet

from .forms import UserCreationForm, LoginForm
from .models import Debate, Contribution, DebateUser


import fair_debate_md as fdmd

from .simple_pages_interface import get_sp, new_sp
from . import simple_pages_content_default as spc
from . import utils

from ipydex import IPS

pjoin = os.path.join

logger = logging.getLogger("fair-debate")
logger.info("module views.py loaded")


class Container:
    pass


class MainView(View):
    def get(self, request):
        context = {
            # nested dict for easier debugging in the template
            "data": {
                "sp": None,
                "utd_page_type": "utd_landing_page",
            }
        }

        if request.user.is_authenticated:
            user: DebateUser = request.user
            debate_list = list(user.debate_as_user_a.all()) + list(user.debate_as_user_b.all())
            #TODO: sort by date
            context["data"]["recent_user_debates"] = debate_list

        context["data"]["sp"] = get_sp("landing")
        # template = "base/main_simplepage.html"
        template = "base/main_landing_page.html"

        return render(request, template, context)

    def post(self, request, **kwargs):

        raise NotImplementedError

@method_decorator(login_required(login_url=f"/{settings.LOGIN_URL}"), name="dispatch")
class NewDebateView(View):
    def get(self, request):

        context = {
            "data": {
                "utd_page_type": "utd_new_debate",
            }
        }
        template = "base/main_new_debate.html"

        # TODO: maybe redirect here
        return render(request, template, context)

    def post(self, request, **kwargs):
        debate_obj = Debate(user_a=request.user)
        debate_obj.save()
        debate_obj.debate_key = f"d{debate_obj.pk}-{request.POST['debate_slug']}"
        debate_obj.save()

        return ShowDebateView().post(request, debate_key=debate_obj.debate_key, contribution_key="a")

        # body_content = request.POST.get("body", "")
        # return self.render_result_from_md(request, body_content)

    def render_result_from_md(self, request, body_content_md):
        raise DeprecationWarning

        mdp = fdmd.MDProcessor(plain_md=body_content_md, convert_now=True)

        context = {
            "data": {
                "utd_page_type": "utd_new_debate",
                "plain_md": mdp.plain_md_src,
                "segmented_html": mdp.segmented_html,
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


class ProcessContribution(View):
    def _preprocess_post(self, request):
        """
        Motivation: if we send a post request via javascript the request.POST-dict is empty.
        -> We construct it manually from the body-data
        """
        if len(request.POST) == 0:
            body_data = json.loads(request.body)
            if not isinstance(body_data, dict):
                msg = f"Unexpected type of parsed request.body: {type(body_data)}"
                raise TypeError(msg)
            request.POST =  QueryDict(urlencode(json.loads(request.body)))

    def post(self, request,  action=None):
        self._preprocess_post(request)
        debate_key = request.POST["debate_key"]
        if action == "commit":
            self.commit_contribution(request)
        elif action == "commit_all":
            self.commit_all_uc_contribution(request)
        elif action == "delete":
            self.delete_contribution(request)
        else:
            msg = f"Unexpected action: ('{action}') for view ProcessContribution"
            error_page(request, title="Error during ProcessContribution", msg=msg)
        return redirect("show_debate", debate_key=debate_key)

    def get(self, request, **kwargs):
        msg = f"Get request not allowed for path {request.path}!"
        return error_page(request, title="Invalid Request", msg=msg, status=403)

    def _get_contribution_set_from_request(self, request, all=False):
        debate_key = request.POST["debate_key"]
        debate_obj = Debate.objects.get(debate_key=debate_key)

        ctb_objs: QuerySet
        if all:
            ctb_objs = debate_obj.contribution_set.all()
        else:
            ctb_key = request.POST["contribution_key"]
            ctb_objs = debate_obj.contribution_set.filter(contribution_key=ctb_key)
            msg = f"Unexpected number of contribution objects ({len(ctb_objs)}) for {debate_key} ctb {ctb_key}"
            assert len(ctb_objs) == 1, msg

        res = Container()
        res.ctb_objs = ctb_objs
        res.debate_key = debate_key

        return res

    def commit_contribution(self, request):
        c = self._get_contribution_set_from_request(request)

        ctb = fdmd.DBContribution(c.ctb_objs[0].contribution_key, c.ctb_objs[0].body)
        fdmd.commit_ctb(settings.REPO_HOST_DIR, c.debate_key, ctb)
        c.ctb_objs[0].delete()

    def commit_all_uc_contribution(self, request):

        c = self._get_contribution_set_from_request(request, all=True)

        ctb_list = []
        ctb_obj: Contribution
        for ctb_obj in c.ctb_objs:
            ctb_list.append(fdmd.DBContribution(ctb_key=ctb_obj.contribution_key, body=ctb_obj.body))

        fdmd.commit_ctb_list(settings.REPO_HOST_DIR, c.debate_key, ctb_list)
        c.ctb_objs.delete()

    def delete_contribution(self, request):
        c = self._get_contribution_set_from_request(request)
        c.ctb_objs.delete()


class ShowDebateView(View):
    def get(self, request, debate_key=None):

        assert debate_key is not None

        ctb_list = self._get_ctb_list_from_db(author=request.user, debate_obj_or_key=debate_key)

        if len(ctb_list) == 1 and ctb_list[0].ctb_key == "a":
            # create the first contribution of a new debate
            new_debate = True
        else:
            new_debate = False

        try:
            ddl = fdmd.load_repo(settings.REPO_HOST_DIR, debate_key, ctb_list=ctb_list, new_debate=new_debate)
        except FileNotFoundError:
            msg = f"No debate with key `{debate_key}` could be found."
            return error_page(request, title="Not Found", msg=msg, status=404)
        return self.render_result_from_html(request, ddl)

    @method_decorator(login_required(login_url=f"/{settings.LOGIN_URL}"))
    def post(self, request, **kwargs):
        """
        Note: this method might be called explicitly with suitable keyword args from NewDebate.post(...).
        """

        if debate_key := kwargs.get("debate_key"):
            pass
        else:
            debate_key = request.POST["debate_key"]
        debate_obj = Debate.objects.get(debate_key=debate_key)

        if contribution_key := kwargs.get("contribution_key"):
            # This never happens but the negated condition would be harder to read
            pass
        else:
            if request.POST["reference_segment"] == "root_segment":
                contribution_key = "a"
            else:
                # the post-request contains an answer e.g. to a2b1a4
                # get contribution key as a2b1a4b
                contribution_key = fdmd.get_answer_contribution_key(request.POST["reference_segment"])
        answer_mode = contribution_key[-1]
        assert answer_mode in ("a", "b")

        user_role = debate_obj.get_user_role(request.user)
        if err_page := self._ensure_suitable_user_role(request, user_role, answer_mode):
            return err_page

        self.create_or_update_contribution(request, debate_obj, contribution_key)

        return redirect("show_debate", debate_key=debate_key)

    def create_or_update_contribution(self, request, debate_obj: Debate, contribution_key: str) -> Contribution:
        """
        return updated existing or new Contribution-object
        """

        contribution_obj: Contribution
        if contribution_obj := utils.get_or_none(debate_obj.contribution_set, contribution_key=contribution_key):
            contribution_obj.body = request.POST["body"]

        else:
            contribution_obj = Contribution(
                author=request.user,
                debate=debate_obj,
                contribution_key=contribution_key,
                body=request.POST["body"],
            )

        if contribution_obj.body == "":
            msg = (
                    f"Unexpectedly received empty body for contribution {contribution_key}. "
                    "-> Contribution ignored."
                )
            raise utils.UsageError(msg)

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

    def render_result_from_html(self, request, ddl: fdmd.DebateDirLoader):

        body_content_html = ddl.final_html
        debate_obj = Debate.objects.get(debate_key=ddl.debate_key)

        if request.user.is_authenticated:
            len_ctb_obj_set = len(debate_obj.contribution_set.filter(author=request.user))
        else:
            len_ctb_obj_set = 0

        context = {
            "data": {
                "utd_page_type": f"utd_new_debate",
                "segmented_html": body_content_html,
                "debate_title": debate_obj.debate_key,  # TODO: the title should come from metadata.toml
                "debate_key": debate_obj.debate_key,
                "user_role": debate_obj.get_user_role(request.user),
                "num_db_ctbs": len_ctb_obj_set,
                "num_answers": ddl.num_answers,
                "deepest_level": len(ddl.level_tree) - 1,  # start level counting at 0
                # make some data available for js api
                "api_data": json.dumps({
                    "delete_url": reverse("delete_contribution"),
                    "commit_url": reverse("commit_contribution"),
                    "commit_all_url": reverse("commit_all_contributions"),
                    "debate_key": debate_obj.debate_key,
                }),
            }
        }
        template = "base/main_show_debate.html"
        return render(request, template, context)


def assertion_error_page(request):
    # serve a page via get request to simplify the display of source code in browser

    assert False, "intentionally raised assertion error"


def debug_page(request):
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
            "server_status_code": status,
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
                    return redirect("landing_page")
            else:
                data["failed_login_attempt"] = True
    else:
        form = LoginForm()
    return render(request, "main_auth_login.html", {"form": form, "data": data})


# logout page
def user_logout(request):
    logout(request)
    return redirect("landing_page")


def user_profile(request):

    context = {
        # nested dict for easier debugging in the template
        "data": {
            "sp": get_sp("user_profile"),
            "utd_page_type": f"utd_user_profile",
        }
    }

    template = "base/main_simplepage.html"

    return render(request, template, context)
