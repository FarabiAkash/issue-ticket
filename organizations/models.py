from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import User


class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="companies_created",
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name


class Project(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects_created",
    )

    class Meta:
        ordering = ["company__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"],
                name="unique_project_name_per_company",
            )
        ]

    def __str__(self):
        return f"{self.company}: {self.name}"


class ProjectMembership(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="unique_project_member",
            )
        ]
        ordering = ["user__username"]

    def __str__(self):
        return f"{self.user} @ {self.project}"

    def clean(self):
        super().clean()
        if not self.user_id or not self.project_id:
            return
        if (
            self.user.role in User.COMPANY_ROLES
            and self.user.company_id != self.project.company_id
        ):
            raise ValidationError(
                "Company users can only join projects from their own company."
            )
        if self.user.role in User.STAFF_ROLES and self.user.company_id is not None:
            raise ValidationError("Staff members cannot belong to a company.")
