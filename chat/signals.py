from django.db.models.signals import post_save
from django.dispatch import receiver

from organizations.models import Project

from .models import ProjectRoom


@receiver(post_save, sender=Project)
def create_project_room(sender, instance, created, **kwargs):
    if created:
        ProjectRoom.objects.get_or_create(project=instance)
