from django.urls import path
from django.conf import settings

from . import views
from . import utils


main_view = views.MainView.as_view

urlpatterns = [
    path("", main_view(), name="landing_page"),
    path("new/", views.NewDebateView.as_view(), name="new_debate"),
    path("new/test", views.test_new_debate, name="test_new_debate"),
    path("d/<slug:debate_key>", views.ShowDebateView.as_view(), name="show_debate"),
    path(
        "d/d1-lorem_ipsum",
        views.ShowDebateView.as_view(),
        name="test_show_debate",
        kwargs={"debate_key": "d1-lorem_ipsum"},
    ),
    path(
        "commit_contribution",
        views.ProcessContribution.as_view(),
        name="commit_contribution",
        kwargs={"action": "commit"},
    ),
    path(
        "commit_all_contributions",
        views.ProcessContribution.as_view(),
        name="commit_all_contributions",
        kwargs={"action": "commit_all"},
    ),
    path(
        "delete_contribution",
        views.ProcessContribution.as_view(),
        name="delete_contribution",
        kwargs={"action": "delete"},
    ),
    path("menu/", views.menu_page, name="menu_page"),
    path("debug/", views.debug_page, name="debug_page"),
    path(utils.ABOUT_PATH, views.about_page, name="about_page"),
    # this is for testing the error handling
    path("error/", views.assertion_error_page, name="error_page"),
    path("error/js", views.js_error_page, name="trigger_js_error"),
    path(settings.LOGIN_URL, views.user_login, name="login"),
    path("signup/", views.user_signup, name="signup"),
    path("logout/", views.user_logout, name="logout"),
    path("profile/", views.user_profile, name="user_profile"),
]
