from django.urls import path

from chat.views import ProjectChatView

from . import views

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="project_list"),
    path("new/", views.ProjectCreateView.as_view(), name="project_create"),
    path("<int:pk>/", views.ProjectDetailView.as_view(), name="project_detail"),
    path("<int:pk>/chat/", ProjectChatView.as_view(), name="project_chat"),
]
