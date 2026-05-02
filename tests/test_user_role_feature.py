import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from base.models import Debate
from base.templatetags.extra_filters import get_user_role
from django.conf import settings

DebateUser = get_user_model()


class TestGetUserRoleFilter(TestCase):
    """Test the get_user_role template filter."""

    def setUp(self):
        self.user = DebateUser.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.debate = Debate.objects.create(
            user_a=self.user,
            discoverability=Debate.Discoverability.PUBLIC
        )
        # Set a valid debate_key (mimic NewDebateView logic)
        self.debate.debate_key = f"d{self.debate.pk}-test-debate"
        self.debate.save()

    def test_get_user_role_returns_a_for_user_a(self):
        """Test that user_a gets role 'a'."""
        role = get_user_role(self.debate, self.user)
        self.assertEqual(role, "a")

    def test_get_user_role_returns_none_for_non_participant(self):
        """Test that non-participants get None (no role)."""
        other_user = DebateUser.objects.create_user(
            username="otheruser",
            password="testpass123"
        )
        role = get_user_role(self.debate, other_user)
        self.assertIsNone(role)


class TestMainViewUserContext(TestCase):
    """Test that MainView passes user to template context."""

    def setUp(self):
        self.client = Client()

    def test_authenticated_user_in_context(self):
        """Test that authenticated user is passed to template context."""
        user = DebateUser.objects.create_user(
            username="viewtestuser",
            password="testpass123"
        )
        self.client.force_login(user)

        # Create at least one debate so the list is populated
        debate = Debate.objects.create(
            user_a=user,
            discoverability=Debate.Discoverability.PUBLIC
        )
        debate.debate_key = f"d{debate.pk}-test-landing-debate"
        debate.save()

        settings.CATCH_EXCEPTIONS = False
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        # The template should have access to the user variable
        self.assertIn(b"user_role_display", response.content)
