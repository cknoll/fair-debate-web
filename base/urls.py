from django.urls import path
from django.conf import settings

from . import views


main_view = views.MainView.as_view

urlpatterns = [
    path("", main_view(), name="landingpage"),
    path("new/", views.NewDebateView.as_view(), name="new_debate"),
    path("new/test", views.test_new_debate, name="test_new_debate"),
    path("d/<slug:debate_key>", views.ShowDebateView.as_view(), name="show_debate"),
    path(
        "d/d1-lorem_ipsum", views.ShowDebateView.as_view(), name="test_show_debate", kwargs={"debate_key": "d1-lorem_ipsum"}
    ),
    path(
        "process_contribution",
        views.ProcessContribution.as_view(),
        name="process_contribution",
        kwargs={"action": "commit"}
    ),

    path("menu/", views.menu_page, name="menupage"),
    path("debug/", views.debugpage, name="debugpage"),
    path("about/", views.about_page, name="aboutpage"),
    # this is for testing the error handling
    path("error/", views.errorpage, name="errorpage"),
    path("error/js", views.js_error_page, name="trigger_js_error"),
    path(settings.LOGIN_URL, views.user_login, name="login"),
    path("signup/", views.user_signup, name="signup"),
    path("logout/", views.user_logout, name="logout"),
]
