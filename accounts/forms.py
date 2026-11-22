from django import forms
from django.contrib.auth.password_validation import validate_password

from .bootstrap import apply_bootstrap
from .models import User


class StaffUserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        strip=False,
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput,
        strip=False,
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "role"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["role"].choices = [
            (User.Role.APPLICATION_ADMIN, User.Role.APPLICATION_ADMIN.label),
            (User.Role.APPLICATION_USER, User.Role.APPLICATION_USER.label),
        ]
        apply_bootstrap(self)

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        validate_password(password, self.instance)
        return password

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class StaffUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "role", "is_active"]

    def __init__(self, *args, actor, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        if self.instance.role == User.Role.SUPER_ADMIN:
            self.fields["role"].choices = [
                (User.Role.SUPER_ADMIN, User.Role.SUPER_ADMIN.label),
            ]
            self.fields["role"].disabled = True
        else:
            self.fields["role"].choices = [
                (User.Role.APPLICATION_ADMIN, User.Role.APPLICATION_ADMIN.label),
                (User.Role.APPLICATION_USER, User.Role.APPLICATION_USER.label),
            ]
        if self.instance.pk == actor.pk:
            self.fields["is_active"].disabled = True
        apply_bootstrap(self)

