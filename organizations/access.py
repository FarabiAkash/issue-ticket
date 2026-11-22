from django.db.models import Q

from accounts.models import User

from .models import Company, Project


def visible_companies(user):
    if user.role in (User.Role.SUPER_ADMIN, User.Role.APPLICATION_ADMIN):
        return Company.objects.all()
    if user.role == User.Role.COMPANY_ADMIN and user.company_id:
        return Company.objects.filter(pk=user.company_id)
    return Company.objects.none()


def visible_projects(user):
    if user.role in (User.Role.SUPER_ADMIN, User.Role.APPLICATION_ADMIN):
        return Project.objects.all()
    if user.role == User.Role.COMPANY_ADMIN and user.company_id:
        return Project.objects.filter(company_id=user.company_id)
    return Project.objects.filter(memberships__user=user).distinct()


def can_create_company(user):
    return user.role in (User.Role.SUPER_ADMIN, User.Role.APPLICATION_ADMIN)


def can_create_project(user):
    return user.role in (User.Role.SUPER_ADMIN, User.Role.COMPANY_ADMIN)


def can_manage_members(user, project):
    if user.role in (User.Role.SUPER_ADMIN, User.Role.APPLICATION_ADMIN):
        return True
    return (
        user.role == User.Role.COMPANY_ADMIN
        and user.company_id == project.company_id
    )


def assignable_users(actor, project):
    if actor.role in (User.Role.SUPER_ADMIN, User.Role.APPLICATION_ADMIN):
        return User.objects.filter(
            Q(role__in=(User.Role.APPLICATION_ADMIN, User.Role.APPLICATION_USER))
            | Q(pk=actor.pk),
            is_active=True,
        ).distinct()
    if can_manage_members(actor, project) and actor.role == User.Role.COMPANY_ADMIN:
        return User.objects.filter(
            company_id=project.company_id,
            role=User.Role.COMPANY_USER,
            is_active=True,
        )
    return User.objects.none()


def is_project_member(user, project):
    return project.memberships.filter(user=user).exists()
