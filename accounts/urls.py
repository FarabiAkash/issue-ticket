from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.StyledLoginView.as_view(), name="login"),
    path("logout/", views.StyledLogoutView.as_view(), name="logout"),
    path(
        "password/",
        views.OwnPasswordChangeView.as_view(),
        name="password_change",
    ),
]
