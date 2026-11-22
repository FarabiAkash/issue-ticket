from django.core.exceptions import PermissionDenied

from accounts.models import User

from .access import assignable_users
from .models import ProjectMembership


def enroll_company_admins(project):
    admins = User.objects.filter(
        company=project.company,
        role=User.Role.COMPANY_ADMIN,
    )
    ProjectMembership.objects.bulk_create(
        [ProjectMembership(project=project, user=admin) for admin in admins],
        ignore_conflicts=True,
    )


def enroll_admin_on_company_projects(user):
    if user.role != User.Role.COMPANY_ADMIN or user.company_id is None:
        return
    ProjectMembership.objects.bulk_create(
        [
            ProjectMembership(project=project, user=user)
            for project in user.company.projects.all()
        ],
        ignore_conflicts=True,
    )


def add_member(actor, project, user):
    if not assignable_users(actor, project).filter(pk=user.pk).exists():
        raise PermissionDenied("You cannot add this person to the project.")
    if (
        user.role in User.COMPANY_ROLES
        and user.company_id != project.company_id
    ):
        raise PermissionDenied("That person belongs to another company.")
    ProjectMembership.objects.get_or_create(project=project, user=user)


def remove_member(actor, project, user):
    if not assignable_users(actor, project).filter(pk=user.pk).exists():
        raise PermissionDenied("You cannot remove this person from the project.")
    ProjectMembership.objects.filter(project=project, user=user).delete()
