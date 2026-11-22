from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.forms import SetPasswordForm
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView

from .bootstrap import apply_bootstrap
from .forms import StaffUserCreateForm, StaffUserUpdateForm
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
    allowed_roles = (User.Role.SUPER_ADMIN,)


class UserCreateView(RoleRequiredMixin, CreateView):
    model = User
    form_class = StaffUserCreateForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy("user_list")
    allowed_roles = (User.Role.SUPER_ADMIN,)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Created {self.object.username}.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New user"
        context["cancel_url"] = reverse_lazy("user_list")
        return context


class UserUpdateView(RoleRequiredMixin, UpdateView):
    model = User
    form_class = StaffUserUpdateForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy("user_list")
    allowed_roles = (User.Role.SUPER_ADMIN,)

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
    allowed_roles = (User.Role.SUPER_ADMIN,)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        self.target = get_object_or_404(User, pk=kwargs["pk"])
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
