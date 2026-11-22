from django.db.models import Count, Q
from django.urls import reverse

from accounts.access import visible_users
from accounts.models import User
from organizations.access import (
    is_project_member,
    visible_companies,
    visible_projects,
)
from organizations.models import ProjectMembership

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


def _percent(part, whole):
    if not whole:
        return 0
    return round(part * 100 / whole)


def dashboard_for(user):
    tickets = visible_tickets(user)
    counts = {status: 0 for status, _label in Ticket.Status.choices}
    for row in tickets.values("status").annotate(total=Count("pk")):
        counts[row["status"]] = row["total"]
    total = sum(counts.values())
    pending = sum(counts[status] for status in Ticket.NOT_COMPLETED)
    tones = {
        Ticket.Status.OPEN: "primary",
        Ticket.Status.IN_PROGRESS: "yellow",
        Ticket.Status.WAITING: "orange",
        Ticket.Status.RESOLVED: "green",
        Ticket.Status.CLOSED: "secondary",
    }
    statuses = [
        {
            "value": status,
            "label": label,
            "count": counts[status],
            "percent": _percent(counts[status], total),
            "tone": tones[status],
        }
        for status, label in Ticket.Status.choices
    ]
    projects = (
        visible_projects(user)
        .select_related("company")
        .annotate(
            ticket_count=Count("tickets", distinct=True),
            pending_count=Count(
                "tickets",
                filter=Q(tickets__status__in=Ticket.NOT_COMPLETED),
                distinct=True,
            ),
        )
        .order_by("-pending_count", "company__name", "name")
    )
    if user.role in (User.Role.SUPER_ADMIN, User.Role.COMPANY_ADMIN):
        people_count = visible_users(user).count()
        people_label = "Users"
        people_url = reverse("user_list")
    else:
        people_count = (
            ProjectMembership.objects.filter(project__in=visible_projects(user))
            .values("user")
            .distinct()
            .count()
        )
        people_label = "People on projects"
        people_url = ""
    show_companies = user.role in (
        User.Role.SUPER_ADMIN,
        User.Role.APPLICATION_ADMIN,
        User.Role.COMPANY_ADMIN,
    )
    return {
        "pending": pending,
        "pending_percent": _percent(pending, total),
        "total_tickets": total,
        "statuses": statuses,
        "projects": projects,
        "project_count": projects.count(),
        "people_count": people_count,
        "people_label": people_label,
        "people_url": people_url,
        "show_companies": show_companies,
        "company_count": visible_companies(user).count() if show_companies else 0,
        "show_company_column": user.role in User.STAFF_ROLES,
    }
