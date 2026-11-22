from django.contrib import admin

from .models import ProjectMessage, ProjectRoom


@admin.register(ProjectRoom)
class ProjectRoomAdmin(admin.ModelAdmin):
    list_display = ("project", "created_at")


@admin.register(ProjectMessage)
class ProjectMessageAdmin(admin.ModelAdmin):
    list_display = ("room", "author", "created_at")
    search_fields = ("body", "author__username")
