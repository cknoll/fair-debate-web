from django.views import View
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.urls import reverse_lazy
from django.forms import ModelForm
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.contrib.auth import authenticate, login, logout

from .forms import UserCreationForm, LoginForm

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

import fair_debate_md as fdmd

from .simple_pages_interface import get_sp, new_sp
from  . import simple_pages_content_default as spc

from ipydex import IPS


# it seems not possible to use `reverse("login")` because the decorator executed too early f
LOGIN_URL = "/login/"


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
        return self.render_result(request, body_content="")

    def post(self, request, **kwargs):
        body_content = request.POST.get("body_content", "")
        return self.render_result(request, body_content)


    def render_result(self, request, body_content):

        md_with_keys, segmented_html = fdmd.convert_plain_md_to_segmented_html(body_content)
        if body_content:
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
    This view simplifies interactive testing
    """

    with open(fdmd.fixtures.txt1_md_fpath) as fp:
            body_content = fp.read()

    return NewDebateView().render_result(request, body_content=body_content)



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
