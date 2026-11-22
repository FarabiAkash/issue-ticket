from django.test import TestCase
from django.urls import reverse

from .models import User


class RoleAccessTests(TestCase):
    def setUp(self):
        self.super_admin = User.objects.create_user(
            "root",
            "root@example.com",
            "S3curePass!",
            role=User.Role.SUPER_ADMIN,
        )
        self.application_admin = User.objects.create_user(
            "applier",
            "applier@example.com",
            "S3curePass!",
            role=User.Role.APPLICATION_ADMIN,
        )

    def test_create_superuser_sets_super_admin_role(self):
        user = User.objects.create_superuser(
            "owner",
            "owner@example.com",
            "S3curePass!",
        )
        self.assertEqual(user.role, User.Role.SUPER_ADMIN)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_anonymous_home_redirects_to_login(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, f"{reverse('login')}?next=/")

    def test_super_admin_can_open_user_list(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse("user_list"))
        self.assertEqual(response.status_code, 200)

    def test_application_admin_cannot_open_user_list(self):
        self.client.force_login(self.application_admin)
        response = self.client.get(reverse("user_list"))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_list_redirects_to_login(self):
        response = self.client.get(reverse("user_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_super_admin_creates_application_user(self):
        self.client.force_login(self.super_admin)
        response = self.client.post(
            reverse("user_create"),
            {
                "username": "agent1",
                "email": "agent1@example.com",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "role": User.Role.APPLICATION_USER,
                "password1": "S3curePass!",
                "password2": "S3curePass!",
            },
        )
        self.assertRedirects(response, reverse("user_list"))
        created = User.objects.get(username="agent1")
        self.assertEqual(created.role, User.Role.APPLICATION_USER)
        self.assertTrue(created.check_password("S3curePass!"))
        self.assertFalse(created.is_superuser)

    def test_super_admin_cannot_create_another_super_admin_from_the_form(self):
        self.client.force_login(self.super_admin)
        response = self.client.post(
            reverse("user_create"),
            {
                "username": "second",
                "email": "second@example.com",
                "role": User.Role.SUPER_ADMIN,
                "password1": "S3curePass!",
                "password2": "S3curePass!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="second").exists())
