from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.forms import SetPasswordForm
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView

from .access import manageable_users, visible_users
from .bootstrap import apply_bootstrap
from .forms import (
    CompanyUserCreateForm,
    CompanyUserUpdateForm,
    StaffUserCreateForm,
    StaffUserUpdateForm,
)
from .mixins import RoleRequiredMixin
from .models import User


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"


class StyledLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_form(self, form_class=None):
        return apply_bootstrap(super().get_form(form_class))


class StyledLogoutView(LogoutView):
    next_page = reverse_lazy("login")


class OwnPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("home")

    def get_form(self, form_class=None):
        return apply_bootstrap(super().get_form(form_class))

    def form_valid(self, form):
        messages.success(self.request, "Password updated.")
        return super().form_valid(form)


class UserListView(RoleRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    paginate_by = 20
    allowed_roles = (User.Role.SUPER_ADMIN, User.Role.COMPANY_ADMIN)

    def get_queryset(self):
        return visible_users(self.request.user)


class UserCreateView(RoleRequiredMixin, CreateView):
    model = User
    template_name = "users/user_form.html"
    success_url = reverse_lazy("user_list")
    allowed_roles = (User.Role.SUPER_ADMIN, User.Role.COMPANY_ADMIN)

    def get_form_class(self):
        if self.request.user.is_company_admin:
            return CompanyUserCreateForm
        return StaffUserCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.user.is_company_admin:
            kwargs["company"] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Created {self.object.username}.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_company_admin:
            context["page_title"] = "New company user"
        else:
            context["page_title"] = "New user"
        context["cancel_url"] = reverse_lazy("user_list")
        return context


class UserUpdateView(RoleRequiredMixin, UpdateView):
    model = User
    template_name = "users/user_form.html"
    success_url = reverse_lazy("user_list")
    allowed_roles = (User.Role.SUPER_ADMIN, User.Role.COMPANY_ADMIN)

    def get_queryset(self):
        return manageable_users(self.request.user)

    def get_form_class(self):
        if self.request.user.is_company_admin:
            return CompanyUserUpdateForm
        return StaffUserUpdateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Updated {self.object.username}.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.username}"
        context["cancel_url"] = reverse_lazy("user_list")
        return context


class UserPasswordView(RoleRequiredMixin, FormView):
    template_name = "users/password_form.html"
    form_class = SetPasswordForm
    success_url = reverse_lazy("user_list")
    allowed_roles = (User.Role.SUPER_ADMIN, User.Role.COMPANY_ADMIN)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role in self.allowed_roles:
            self.target = get_object_or_404(
                manageable_users(request.user),
                pk=kwargs["pk"],
            )
            if request.user.pk == self.target.pk:
                return redirect("password_change")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.target
        return kwargs

    def get_form(self, form_class=None):
        return apply_bootstrap(super().get_form(form_class))

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f"Password updated for {self.target.username}.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Set password for {self.target.username}"
        context["cancel_url"] = reverse_lazy("user_list")
        return context
