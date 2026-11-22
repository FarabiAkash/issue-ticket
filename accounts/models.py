from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
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

    objects = UserManager()

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return self.username

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
