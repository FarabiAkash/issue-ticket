from accounts.models import User
from organizations.access import is_project_member, visible_projects

from .models import Ticket


def visible_tickets(user):
    if user.role in (User.Role.SUPER_ADMIN, User.Role.APPLICATION_ADMIN):
        return Ticket.objects.all()
    if user.role == User.Role.COMPANY_ADMIN and user.company_id:
        return Ticket.objects.filter(project__company_id=user.company_id)
    return Ticket.objects.filter(project__memberships__user=user).distinct()


def projects_for_new_ticket(user):
    if user.role == User.Role.SUPER_ADMIN:
        return visible_projects(user)
    if user.role in (User.Role.COMPANY_ADMIN, User.Role.COMPANY_USER):
        return visible_projects(user).filter(memberships__user=user).distinct()
    return visible_projects(user).none()


def can_create_ticket(user, project):
    return projects_for_new_ticket(user).filter(pk=project.pk).exists()


def can_change_status(user, ticket):
    if user.role in (User.Role.SUPER_ADMIN, User.Role.APPLICATION_ADMIN):
        return True
    if user.role == User.Role.APPLICATION_USER:
        return is_project_member(user, ticket.project)
    return False


def recent_tickets(user):
    tickets = visible_tickets(user).select_related(
        "project",
        "project__company",
        "created_by",
    )
    if user.role in User.STAFF_ROLES:
        tickets = tickets.filter(status__in=Ticket.NOT_COMPLETED)
    return tickets.order_by("-updated_at")[:8]
