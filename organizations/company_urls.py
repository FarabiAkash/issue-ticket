from django.urls import path

from . import views

urlpatterns = [
    path("", views.CompanyListView.as_view(), name="company_list"),
    path("new/", views.CompanyCreateView.as_view(), name="company_create"),
    path("<int:pk>/", views.CompanyDetailView.as_view(), name="company_detail"),
    path(
        "<int:pk>/admins/new/",
        views.CompanyAdminCreateView.as_view(),
        name="company_admin_create",
    ),
]
