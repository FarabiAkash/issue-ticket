from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from accounts.models import User
from chat.routing import websocket_urlpatterns
from organizations.models import Company, Project
from organizations.services import enroll_company_admins


class ProjectChatPageTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Acme")
        self.project = Project.objects.create(company=self.company, name="Website")
        self.member = User.objects.create_user(
            "acme-admin",
            "admin@example.com",
            "S3curePass!",
            role=User.Role.COMPANY_ADMIN,
            company=self.company,
        )
        self.outsider = User.objects.create_user(
            "applier",
            "applier@example.com",
            "S3curePass!",
            role=User.Role.APPLICATION_ADMIN,
        )
        enroll_company_admins(self.project)

    def test_member_can_open_the_room(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("project_chat", args=[self.project.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Project chat")

    def test_non_member_cannot_open_the_room(self):
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("project_chat", args=[self.project.pk]))
        self.assertEqual(response.status_code, 404)
        detail = self.client.get(reverse("project_detail", args=[self.project.pk]))
        self.assertNotContains(detail, "Project chat")


class ProjectChatSocketTests(TransactionTestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Acme")
        self.project = Project.objects.create(company=self.company, name="Website")
        self.member = User.objects.create_user(
            "acme-user",
            "user@example.com",
            "S3curePass!",
            role=User.Role.COMPANY_USER,
            company=self.company,
        )
        self.outsider = User.objects.create_user(
            "agent",
            "agent@example.com",
            "S3curePass!",
            role=User.Role.APPLICATION_USER,
        )
        self.project.memberships.create(user=self.member)

    async def test_member_message_is_saved_and_broadcast(self):
        communicator = WebsocketCommunicator(
            URLRouter(websocket_urlpatterns),
            f"/ws/projects/{self.project.pk}/chat/",
        )
        communicator.scope["user"] = self.member
        connected, _closed = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to({"body": "Hello team"})
        payload = await communicator.receive_json_from()
        self.assertEqual(payload["body"], "Hello team")
        self.assertEqual(payload["author"], "acme-user")
        await communicator.disconnect()
        saved = await sync_to_async(
            self.project.room.messages.filter(body="Hello team").exists
        )()
        self.assertTrue(saved)

    async def test_non_member_is_rejected(self):
        communicator = WebsocketCommunicator(
            URLRouter(websocket_urlpatterns),
            f"/ws/projects/{self.project.pk}/chat/",
        )
        communicator.scope["user"] = self.outsider
        connected, _closed = await communicator.connect()
        self.assertFalse(connected)
