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
from .models import Debate, Contribution


import fair_debate_md as fdmd

from .simple_pages_interface import get_sp, new_sp
from  . import simple_pages_content_default as spc

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
                "unit_test_comment": f"utc_landingpage",
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
                "unit_test_comment": f"utc_new_debate",
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
    def get(self, request, test=False):

        if not test:
            msg = "show debate is only implemented for test content"
            return error_page(request, "NotImplemented", msg)

        # Show the display (show) mode with some preloaded fixture data (containing answers)
        # This view simplifies interactive testing during development
        TEST_DEBATE_DIR1 = pjoin(fdmd.fixtures.path, "debate1")
        ddl = fdmd.load_dir(TEST_DEBATE_DIR1)
        return self.render_result_from_html(request, body_content_html=ddl.final_html, debate_key=ddl.debate_key)

    @method_decorator(login_required(login_url=f"/{settings.LOGIN_URL}"))
    def post(self, request, **kwargs):

        TEST_DEBATE_DIR1 = pjoin(fdmd.fixtures.path, "debate1")
        ddl: fdmd.DebateDirLoader = fdmd.load_dir(TEST_DEBATE_DIR1)
        ensure_test_data_existence()

        debate_key = request.POST["debate_key"]
        debate_obj = Debate.objects.get(debate_key=debate_key)

        new_contribution = Contribution(
            author=request.user,
            debate = debate_obj,
            contribution_key = fdmd.get_answer_contribution_key(request.POST["reference_segment"]),
            body=request.POST["body"]
        )

        IPS()

        return self.render_result_from_html(request, body_content_html=ddl.final_html, debate_key=ddl.debate_key)

    def render_result_from_html(self, request, body_content_html, debate_key: str):

        context = {
            "data": {
                "unit_test_comment": f"utc_new_debate",
                "segmented_html": body_content_html,
                "debate_title": "untitled debate",
                "debate_key": debate_key,
            }
        }
        template = "base/main_show_debate.html"

        # TODO: maybe redirect here
        return render(request, template, context)


# TODO move this to fixtures
def ensure_test_data_existence():
    """
    Quick and dirty way to ensure that the necessary test data exists
    """

    try:
        Debate.objects.get(debate_key=fdmd.TEST_DEBATE_KEY)
    except (ObjectDoesNotExist, OperationalError):
        new_obj = Debate(debate_key=fdmd.TEST_DEBATE_KEY)
        new_obj.save()

def errorpage(request):
    # serve a page via get request to simplify the display of source code in browser

    assert False, "intentionally raised assertion error"

def debugpage(request):
    # serve a page via get request to simplify the display of source code in browser
    msg="this is a debug page<br><br>\n"*10
    return error_page(request, title="debug page", msg=msg, status=200)


def error_page(request, title, msg, status=500):
        sp_type = title.lower().replace(" ", "_")
        sp = new_sp(
            type=sp_type,
            title=title,
            # TODO handle translation (we can not simple use
            # django.utils.translation.gettext here)
            content=msg
        )

        context = {
            # nested dict for easier debugging in the template
            "data": {
                "sp": sp,
                "main_class": "error_container",
                "unit_test_comment": f"utc_{sp_type}",
            }
        }

        template = "base/main_simplepage.html"

        return render(request, template, context, status=status)

def about_page(request):

        context = {
            # nested dict for easier debugging in the template
            "data": {
                "sp": get_sp("about"),
                # "main_class": "error_container",
                "unit_test_comment": f"utc_about_page",
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
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'main_auth_signup.html', {'form': form})

# login page
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('landingpage')
    else:
        form = LoginForm()
    return render(request, 'main_auth_login.html', {'form': form})

# logout page
def user_logout(request):
    logout(request)
    return redirect('landingpage')

# End of medium source
