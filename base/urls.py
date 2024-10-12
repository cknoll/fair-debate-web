from django.urls import path

from . import views


main_view = views.MainView.as_view

urlpatterns = [
    path("", main_view(), name="landingpage"),

    path("new/", views.NewDebateView.as_view(), name="new_debate"),
    path("new/test", views.test_new_debate, name="test_new_debate"),
    path("menu/", views.menu_page, name="menupage"),
    path("debug/", views.debugpage, name="debugpage"),
    path("about/", views.about_page, name="aboutpage"),
    # this is for testing the error handling
    path("error/", views.errorpage, name="errorpage"),

    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
]
