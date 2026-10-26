
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import ScrollSession, BreakEvent, UserGoal


class ScrollBrakeModelTests(TestCase):
    def test_models_are_available(self):
        self.assertIsNotNone(ScrollSession)
        self.assertIsNotNone(BreakEvent)
        self.assertIsNotNone(UserGoal)

    def test_user_can_be_created(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="testuser",
            password="test-password-123"
        )
        self.assertEqual(user.username, "testuser")
