# Source: https://medium.com/@devsumitg/django-auth-user-signup-and-login-7b424dae7fab

from django import forms
from django.contrib.auth.forms import UserCreationForm
from . import models


class SignupForm(UserCreationForm):
    class Meta:
        model = models.DebateUser
        fields = ["username", "password1", "password2"]


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


# End of medium source
