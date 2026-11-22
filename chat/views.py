from django.views.generic import DetailView

from accounts.mixins import RoleRequiredMixin
from accounts.models import User
from organizations.models import Project

from .models import ProjectRoom


class ProjectChatView(RoleRequiredMixin, DetailView):
    model = Project
    template_name = "chat/project_chat.html"
    context_object_name = "project"
    allowed_roles = User.Role.values

    def get_queryset(self):
        return Project.objects.filter(
            memberships__user=self.request.user,
            memberships__user__is_active=True,
        ).select_related("company")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room, _created = ProjectRoom.objects.get_or_create(project=self.object)
        latest = list(room.messages.select_related("author").order_by("-created_at")[:200])
        latest.reverse()
        context["chat_messages"] = latest
        return context
