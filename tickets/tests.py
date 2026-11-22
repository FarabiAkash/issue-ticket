import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from accounts.models import User
from organizations.models import Company, Project
from organizations.services import enroll_company_admins

from .models import Ticket, TicketNote


def png_upload(name="shot.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), "red").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class TicketAccessTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Acme")
        self.project = Project.objects.create(company=self.company, name="Website")
        self.company_admin = User.objects.create_user(
            "acme-admin",
            "admin@example.com",
            "S3curePass!",
            role=User.Role.COMPANY_ADMIN,
            company=self.company,
        )
        self.company_user = User.objects.create_user(
            "acme-user",
            "user@example.com",
            "S3curePass!",
            role=User.Role.COMPANY_USER,
            company=self.company,
        )
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
        enroll_company_admins(self.project)
        self.project.memberships.create(user=self.company_user)
        self.project.memberships.create(user=self.application_user)

    def test_company_user_creates_ticket_with_screenshot(self):
        self.client.force_login(self.company_user)
        response = self.client.post(
            reverse("ticket_create"),
            {
                "project": self.project.pk,
                "title": "Login fails",
                "description": "The form returns a 500.",
                "images": png_upload(),
            },
        )
        ticket = Ticket.objects.get(title="Login fails")
        self.assertRedirects(response, reverse("ticket_detail", args=[ticket.pk]))
        self.assertEqual(ticket.attachments.count(), 1)
        self.assertEqual(ticket.created_by, self.company_user)

    def test_rejects_non_image_upload(self):
        self.client.force_login(self.company_user)
        upload = SimpleUploadedFile("notes.txt", b"hello", content_type="text/plain")
        response = self.client.post(
            reverse("ticket_create"),
            {
                "project": self.project.pk,
                "title": "Bad file",
                "description": "Should not save.",
                "images": upload,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ticket.objects.filter(title="Bad file").exists())

    def test_application_user_updates_status_and_company_user_cannot(self):
        ticket = Ticket.objects.create(
            project=self.project,
            title="Outage",
            description="Site is down.",
            created_by=self.company_user,
        )
        self.client.force_login(self.company_user)
        denied = self.client.post(
            reverse("ticket_detail", args=[ticket.pk]),
            {"action": "status", "status": Ticket.Status.RESOLVED},
        )
        self.assertEqual(denied.status_code, 403)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.Status.OPEN)

        self.client.force_login(self.application_user)
        response = self.client.post(
            reverse("ticket_detail", args=[ticket.pk]),
            {"action": "status", "status": Ticket.Status.IN_PROGRESS},
        )
        self.assertRedirects(response, reverse("ticket_detail", args=[ticket.pk]))
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.Status.IN_PROGRESS)
        self.assertTrue(
            TicketNote.objects.filter(
                ticket=ticket,
                kind=TicketNote.Kind.STATUS,
            ).exists()
        )

    def test_staff_queue_hides_completed_tickets_by_default(self):
        Ticket.objects.create(
            project=self.project,
            title="Still open",
            description="Open work.",
            created_by=self.company_user,
        )
        Ticket.objects.create(
            project=self.project,
            title="Already done",
            description="Finished.",
            status=Ticket.Status.RESOLVED,
            created_by=self.company_user,
        )
        self.client.force_login(self.application_admin)
        response = self.client.get(reverse("ticket_list"))
        self.assertContains(response, "Still open")
        self.assertNotContains(response, "Already done")

    def test_unassigned_application_user_cannot_open_the_ticket(self):
        outsider = User.objects.create_user(
            "other-agent",
            "other@example.com",
            "S3curePass!",
            role=User.Role.APPLICATION_USER,
        )
        ticket = Ticket.objects.create(
            project=self.project,
            title="Private",
            description="Members only.",
            created_by=self.company_user,
        )
        self.client.force_login(outsider)
        response = self.client.get(reverse("ticket_detail", args=[ticket.pk]))
        self.assertEqual(response.status_code, 404)

    def test_application_user_cannot_create_a_ticket(self):
        self.client.force_login(self.application_user)
        response = self.client.get(reverse("ticket_create"))
        self.assertEqual(response.status_code, 403)
