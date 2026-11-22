from django import forms
from django.contrib.auth.password_validation import validate_password

from accounts.bootstrap import apply_bootstrap
from accounts.forms import CompanyAdminCreateForm
from accounts.models import User

from .models import Company, Project


class CompanyCreateForm(forms.Form):
    company_name = forms.CharField(max_length=200)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
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
    user_limit = forms.IntegerField(
        label="User limit",
        min_value=0,
        required=False,
        initial=10,
        help_text="How many company users this company can create. Defaults to 10.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap(self)

    def clean_company_name(self):
        name = self.cleaned_data["company_name"].strip()
        if Company.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("A company with this name already exists.")
        return name

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def clean_user_limit(self):
        value = self.cleaned_data.get("user_limit")
        if value is None:
            return 10
        return value

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned

    def save(self, actor):
        company = Company.objects.create(
            name=self.cleaned_data["company_name"],
            created_by=actor,
            user_limit=self.cleaned_data["user_limit"],
        )
        admin_form = CompanyAdminCreateForm(
            data={
                "username": self.cleaned_data["username"],
                "email": self.cleaned_data["email"],
                "first_name": self.cleaned_data["first_name"],
                "last_name": self.cleaned_data["last_name"],
                "password1": self.cleaned_data["password1"],
                "password2": self.cleaned_data["password2"],
            },
            company=company,
        )
        if not admin_form.is_valid():
            raise forms.ValidationError(admin_form.errors.as_text())
        admin_form.save()
        return company


class CompanyUserLimitForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["user_limit"]
        labels = {"user_limit": "User limit"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user_limit"].help_text = (
            "How many company users this company can create."
        )
        apply_bootstrap(self)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["company", "name", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, actor, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        if actor.role == User.Role.COMPANY_ADMIN:
            self.fields.pop("company")
        else:
            self.fields["company"].queryset = Company.objects.all()
        apply_bootstrap(self)

    def clean(self):
        cleaned = super().clean()
        name = (cleaned.get("name") or "").strip()
        cleaned["name"] = name
        if self.actor.role == User.Role.COMPANY_ADMIN:
            company = self.actor.company
        else:
            company = cleaned.get("company")
        if name and company:
            taken = Project.objects.filter(company=company, name=name)
            if self.instance.pk:
                taken = taken.exclude(pk=self.instance.pk)
            if taken.exists():
                self.add_error("name", "This company already has a project with that name.")
        return cleaned

    def save(self, commit=True):
        is_new = self.instance.pk is None
        project = super().save(commit=False)
        if self.actor.role == User.Role.COMPANY_ADMIN:
            project.company = self.actor.company
        if is_new:
            project.created_by = self.actor
        if commit:
            project.save()
        return project


class AddMemberForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.none(), label="Person")

    def __init__(self, *args, actor, project, **kwargs):
        super().__init__(*args, **kwargs)
        from .access import assignable_users

        self.fields["user"].queryset = assignable_users(actor, project).exclude(
            pk__in=project.memberships.values("user_id")
        )
        apply_bootstrap(self)
