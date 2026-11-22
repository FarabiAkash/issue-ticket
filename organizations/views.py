from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView
from django.views.generic.edit import CreateView

from accounts.forms import CompanyAdminCreateForm
from accounts.mixins import RoleRequiredMixin
from accounts.models import User

from .access import (
    assignable_users,
    can_create_company,
    can_create_project,
    can_manage_members,
    is_project_member,
    visible_companies,
    visible_projects,
)
from .forms import AddMemberForm, CompanyCreateForm, ProjectForm
from .models import Company, Project
from .services import (
    add_member,
    enroll_admin_on_company_projects,
    enroll_company_admins,
    remove_member,
)


class CompanyAccessMixin(RoleRequiredMixin):
    allowed_roles = (
        User.Role.SUPER_ADMIN,
        User.Role.APPLICATION_ADMIN,
        User.Role.COMPANY_ADMIN,
    )


class CompanyListView(CompanyAccessMixin, ListView):
    model = Company
    template_name = "companies/company_list.html"
    context_object_name = "companies"

    def get_queryset(self):
        return visible_companies(self.request.user).annotate(
            project_count=Count("projects")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_create_company"] = can_create_company(self.request.user)
        return context


class CompanyCreateView(CompanyAccessMixin, FormView):
    form_class = CompanyCreateForm
    template_name = "companies/company_form.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not can_create_company(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        with transaction.atomic():
            company = form.save(self.request.user)
        messages.success(self.request, f"Created {company.name}.")
        return redirect("company_detail", pk=company.pk)


class CompanyDetailView(CompanyAccessMixin, DetailView):
    model = Company
    template_name = "companies/company_detail.html"
    context_object_name = "company"

    def get_queryset(self):
        return visible_companies(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["admins"] = self.object.users.filter(role=User.Role.COMPANY_ADMIN)
        context["projects"] = self.object.projects.all()
        context["can_add_admin"] = can_create_company(self.request.user)
        return context


class CompanyAdminCreateView(CompanyAccessMixin, CreateView):
    model = User
    form_class = CompanyAdminCreateForm
    template_name = "users/user_form.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not can_create_company(request.user):
            raise PermissionDenied
        self.company = get_object_or_404(visible_companies(request.user), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["company"] = self.company
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            user = form.save()
            enroll_admin_on_company_projects(user)
        messages.success(self.request, f"Created company admin {user.username}.")
        return redirect("company_detail", pk=self.company.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"New company admin for {self.company.name}"
        context["cancel_url"] = reverse("company_detail", kwargs={"pk": self.company.pk})
        return context


class ProjectAccessMixin(RoleRequiredMixin):
    allowed_roles = (
        User.Role.SUPER_ADMIN,
        User.Role.APPLICATION_ADMIN,
        User.Role.APPLICATION_USER,
        User.Role.COMPANY_ADMIN,
        User.Role.COMPANY_USER,
    )


class ProjectListView(ProjectAccessMixin, ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        return (
            visible_projects(self.request.user)
            .select_related("company")
            .annotate(member_count=Count("memberships"))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_create_project"] = can_create_project(self.request.user)
        return context


class ProjectCreateView(ProjectAccessMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not can_create_project(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            project = form.save()
            enroll_company_admins(project)
        messages.success(self.request, f"Created {project.name}.")
        return redirect("project_detail", pk=project.pk)


class ProjectDetailView(ProjectAccessMixin, DetailView):
    model = Project
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return visible_projects(self.request.user).select_related("company")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        project = self.object
        if not can_manage_members(request.user, project):
            raise PermissionDenied
        action = request.POST.get("action")
        if action == "add":
            form = AddMemberForm(request.POST, actor=request.user, project=project)
            if form.is_valid():
                add_member(request.user, project, form.cleaned_data["user"])
                messages.success(request, "Member added.")
                return redirect("project_detail", pk=project.pk)
            return self.render_to_response(self.get_context_data(add_form=form))
        if action == "remove":
            user = get_object_or_404(User, pk=request.POST.get("user"))
            remove_member(request.user, project, user)
            messages.success(request, "Member removed.")
            return redirect("project_detail", pk=project.pk)
        raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        context["memberships"] = project.memberships.select_related("user")
        context["can_manage_members"] = can_manage_members(self.request.user, project)
        context["is_member"] = is_project_member(self.request.user, project)
        if context["can_manage_members"] and "add_form" not in context:
            context["add_form"] = AddMemberForm(
                actor=self.request.user,
                project=project,
            )
        if context["can_manage_members"]:
            context["removable_ids"] = set(
                assignable_users(self.request.user, project)
                .filter(pk__in=project.memberships.values("user_id"))
                .values_list("pk", flat=True)
            )
        return context
