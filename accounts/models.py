from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.core.exceptions import ValidationError
from django.db import models


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.SUPER_ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        APPLICATION_ADMIN = "application_admin", "Application Admin"
        APPLICATION_USER = "application_user", "Application User"
        COMPANY_ADMIN = "company_admin", "Company Admin"
        COMPANY_USER = "company_user", "Company User"

    STAFF_ROLES = (
        Role.SUPER_ADMIN,
        Role.APPLICATION_ADMIN,
        Role.APPLICATION_USER,
    )
    COMPANY_ROLES = (
        Role.COMPANY_ADMIN,
        Role.COMPANY_USER,
    )

    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.APPLICATION_USER,
        db_index=True,
    )
    company = models.ForeignKey(
        "organizations.Company",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="users",
    )

    objects = UserManager()

    class Meta:
        ordering = ["username"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        role__in=["company_admin", "company_user"],
                        company__isnull=False,
                    )
                    | models.Q(
                        role__in=[
                            "super_admin",
                            "application_admin",
                            "application_user",
                        ],
                        company__isnull=True,
                    )
                ),
                name="user_company_matches_role",
            )
        ]

    def __str__(self):
        return self.username

    def clean(self):
        super().clean()
        if self.role in self.COMPANY_ROLES and self.company_id is None:
            raise ValidationError(
                {"company": "Company roles must belong to a company."}
            )
        if self.role in self.STAFF_ROLES and self.company_id is not None:
            raise ValidationError(
                {"company": "Staff roles cannot belong to a company."}
            )

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_application_admin(self):
        return self.role == self.Role.APPLICATION_ADMIN

    @property
    def is_application_staff(self):
        return self.role in self.STAFF_ROLES

    @property
    def is_company_admin(self):
        return self.role == self.Role.COMPANY_ADMIN

    @property
    def is_company_user(self):
        return self.role == self.Role.COMPANY_USER
