from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView

from accounts.mixins import RoleRequiredMixin
from accounts.models import User
from organizations.access import visible_projects

from .access import can_change_status, projects_for_new_ticket, visible_tickets
from .forms import NoteForm, StatusForm, TicketCreateForm, validate_ticket_image
from .models import Ticket, TicketAttachment, TicketNote


class TicketAccessMixin(RoleRequiredMixin):
    allowed_roles = User.Role.values


class TicketListView(TicketAccessMixin, ListView):
    model = Ticket
    template_name = "tickets/ticket_list.html"
    context_object_name = "tickets"
    paginate_by = 20

    def get_queryset(self):
        tickets = visible_tickets(self.request.user).select_related(
            "project",
            "project__company",
            "created_by",
        )
        project_id = self.request.GET.get("project")
        if project_id:
            tickets = tickets.filter(project_id=project_id)
        status = self.request.GET.get("status")
        if status is None and self.request.user.role in User.STAFF_ROLES:
            status = "not_completed"
        if status == "not_completed":
            tickets = tickets.filter(status__in=Ticket.NOT_COMPLETED)
        elif status and status != "all":
            tickets = tickets.filter(status=status)
        return tickets

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.request.GET.get("status")
        if status is None and self.request.user.role in User.STAFF_ROLES:
            status = "not_completed"
        context["current_status"] = status or "all"
        context["selected_project"] = self.request.GET.get("project", "")
        context["projects"] = visible_projects(self.request.user).select_related(
            "company"
        )
        context["statuses"] = Ticket.Status.choices
        context["can_create"] = (
            self.request.user.role
            in (
                User.Role.SUPER_ADMIN,
                User.Role.COMPANY_ADMIN,
                User.Role.COMPANY_USER,
            )
        )
        return context


class TicketCreateView(TicketAccessMixin, CreateView):
    model = Ticket
    form_class = TicketCreateForm
    template_name = "tickets/ticket_form.html"
    allowed_roles = (
        User.Role.SUPER_ADMIN,
        User.Role.COMPANY_ADMIN,
        User.Role.COMPANY_USER,
    )

    def get_initial(self):
        initial = super().get_initial()
        project_id = self.request.GET.get("project")
        if project_id:
            initial["project"] = project_id
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def form_valid(self, form):
        uploads = self.request.FILES.getlist("images")
        image_errors = []
        for uploaded in uploads:
            try:
                validate_ticket_image(uploaded)
            except ValidationError as exc:
                image_errors.extend(exc.messages)
        if image_errors:
            for error in image_errors:
                form.add_error(None, error)
            return self.form_invalid(form)
        if not projects_for_new_ticket(self.request.user).filter(
            pk=form.instance.project_id
        ).exists():
            raise PermissionDenied
        ticket = form.save(commit=False)
        ticket.created_by = self.request.user
        ticket.save()
        for uploaded in uploads:
            TicketAttachment.objects.create(
                ticket=ticket,
                image=uploaded,
                uploaded_by=self.request.user,
            )
        messages.success(self.request, "Ticket created.")
        return redirect("ticket_detail", pk=ticket.pk)


class TicketDetailView(TicketAccessMixin, DetailView):
    model = Ticket
    template_name = "tickets/ticket_detail.html"
    context_object_name = "ticket"

    def get_queryset(self):
        return visible_tickets(self.request.user).select_related(
            "project",
            "project__company",
            "created_by",
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get("action")
        if action == "comment":
            return self._add_comment()
        if action == "status":
            return self._change_status()
        if action == "images":
            return self._add_images()
        raise PermissionDenied

    def _add_comment(self):
        form = NoteForm(self.request.POST)
        if form.is_valid():
            TicketNote.objects.create(
                ticket=self.object,
                author=self.request.user,
                body=form.cleaned_data["body"],
                kind=TicketNote.Kind.COMMENT,
            )
            messages.success(self.request, "Note added.")
            return redirect("ticket_detail", pk=self.object.pk)
        return self.render_to_response(self.get_context_data(note_form=form))

    def _change_status(self):
        if not can_change_status(self.request.user, self.object):
            raise PermissionDenied
        form = StatusForm(self.request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(status_form=form))
        new_status = form.cleaned_data["status"]
        if new_status == self.object.status:
            return redirect("ticket_detail", pk=self.object.pk)
        previous = self.object.get_status_display()
        self.object.status = new_status
        self.object.save(update_fields=["status", "updated_at"])
        TicketNote.objects.create(
            ticket=self.object,
            author=self.request.user,
            body=f"Status changed from {previous} to {self.object.get_status_display()}.",
            kind=TicketNote.Kind.STATUS,
        )
        messages.success(self.request, "Status updated.")
        return redirect("ticket_detail", pk=self.object.pk)

    def _add_images(self):
        uploads = self.request.FILES.getlist("images")
        if not uploads:
            messages.error(self.request, "Choose an image to upload.")
            return redirect("ticket_detail", pk=self.object.pk)
        saved = 0
        for uploaded in uploads:
            try:
                validate_ticket_image(uploaded)
            except ValidationError as exc:
                messages.error(self.request, " ".join(exc.messages))
                continue
            TicketAttachment.objects.create(
                ticket=self.object,
                image=uploaded,
                uploaded_by=self.request.user,
            )
            saved += 1
        if saved:
            messages.success(self.request, "Screenshot added.")
        return redirect("ticket_detail", pk=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket = self.object
        context["notes"] = ticket.notes.select_related("author")
        context["attachments"] = ticket.attachments.all()
        context["can_change_status"] = can_change_status(self.request.user, ticket)
        if "note_form" not in context:
            context["note_form"] = NoteForm()
        if context["can_change_status"] and "status_form" not in context:
            context["status_form"] = StatusForm(initial={"status": ticket.status})
        return context

    def get_success_url(self):
        return reverse("ticket_detail", kwargs={"pk": self.object.pk})
