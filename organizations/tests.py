from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Company, Project, ProjectMembership
from .services import add_member, enroll_company_admins


class OrganizationAccessTests(TestCase):
    def setUp(self):
        self.application_admin = User.objects.create_user(
            "applier",
            "applier@example.com",
            "S3curePass!",
            role=User.Role.APPLICATION_ADMIN,
        )
        self.application_user = User.objects.create_user(
            "agent",
            "agent@example.com",
            "S3curePass!",
            role=User.Role.APPLICATION_USER,
        )
        self.client.force_login(self.application_admin)
        self.client.post(
            reverse("company_create"),
            {
                "company_name": "Acme",
                "username": "acme-admin",
                "email": "acme@example.com",
                "first_name": "Ace",
                "last_name": "Admin",
                "password1": "S3curePass!",
                "password2": "S3curePass!",
            },
        )
        self.company = Company.objects.get(name="Acme")
        self.company_admin = User.objects.get(username="acme-admin")

    def test_application_admin_creates_company_and_admin(self):
        self.assertEqual(self.company_admin.role, User.Role.COMPANY_ADMIN)
        self.assertEqual(self.company_admin.company, self.company)

    def test_company_admin_creates_project_and_is_a_member(self):
        self.client.force_login(self.company_admin)
        response = self.client.post(
            reverse("project_create"),
            {"name": "Website", "description": "Public site"},
        )
        project = Project.objects.get(name="Website")
        self.assertRedirects(response, reverse("project_detail", args=[project.pk]))
        self.assertTrue(
            ProjectMembership.objects.filter(
                project=project,
                user=self.company_admin,
            ).exists()
        )

    def test_application_admin_cannot_create_a_project(self):
        self.client.force_login(self.application_admin)
        response = self.client.get(reverse("project_create"))
        self.assertEqual(response.status_code, 403)

    def test_company_user_can_create_tickets_only_after_assignment(self):
        project = Project.objects.create(company=self.company, name="Website")
        enroll_company_admins(project)
        self.client.force_login(self.company_admin)
        self.client.post(
            reverse("user_create"),
            {
                "username": "acme-user",
                "email": "user@example.com",
                "password1": "S3curePass!",
                "password2": "S3curePass!",
            },
        )
        company_user = User.objects.get(username="acme-user")
        self.assertEqual(company_user.role, User.Role.COMPANY_USER)
        self.client.force_login(company_user)
        self.assertEqual(self.client.get(reverse("company_list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("project_list")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("project_detail", args=[project.pk])).status_code,
            404,
        )
        self.client.force_login(self.company_admin)
        response = self.client.post(
            reverse("project_detail", args=[project.pk]),
            {"action": "add", "user": company_user.pk},
        )
        self.assertRedirects(response, reverse("project_detail", args=[project.pk]))
        self.client.force_login(company_user)
        self.assertEqual(
            self.client.get(reverse("project_detail", args=[project.pk])).status_code,
            200,
        )

    def test_staff_can_be_assigned_and_outsiders_cannot(self):
        project = Project.objects.create(company=self.company, name="Website")
        enroll_company_admins(project)
        self.client.force_login(self.application_admin)
        response = self.client.post(
            reverse("project_detail", args=[project.pk]),
            {"action": "add", "user": self.application_user.pk},
        )
        self.assertRedirects(response, reverse("project_detail", args=[project.pk]))
        other = Company.objects.create(name="Other")
        outsider = User.objects.create_user(
            "outsider",
            "out@example.com",
            "S3curePass!",
            role=User.Role.COMPANY_USER,
            company=other,
        )
        with self.assertRaises(PermissionDenied):
            add_member(self.application_admin, project, outsider)

    def test_new_company_admin_joins_existing_projects(self):
        project = Project.objects.create(company=self.company, name="Website")
        enroll_company_admins(project)
        self.client.force_login(self.application_admin)
        self.client.post(
            reverse("company_admin_create", args=[self.company.pk]),
            {
                "username": "second-admin",
                "email": "second@example.com",
                "password1": "S3curePass!",
                "password2": "S3curePass!",
            },
        )
        second = User.objects.get(username="second-admin")
        self.assertTrue(
            ProjectMembership.objects.filter(project=project, user=second).exists()
        )

    def test_company_admin_cannot_open_another_company(self):
        other = Company.objects.create(name="Other")
        self.client.force_login(self.company_admin)
        response = self.client.get(reverse("company_detail", args=[other.pk]))
        self.assertEqual(response.status_code, 404)
