from django.conf import settings
from django.db import models


class ProjectRoom(models.Model):
    project = models.OneToOneField(
        "organizations.Project",
        on_delete=models.CASCADE,
        related_name="room",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat for {self.project}"


class ProjectMessage(models.Model):
    room = models.ForeignKey(
        ProjectRoom,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="project_messages",
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author}: {self.body[:40]}"
