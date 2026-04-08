"""
This module enables the command `python manage.py setpassword <username> <password>` (used in `deploy.py`).
"""

from io import StringIO

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model



class Command(BaseCommand):
    help = 'set password for user'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)

    def handle(self, *args, **options):
        # evaluate positional arguments
        self.username, self.password = args
        User = get_user_model()
        user = User.objects.get(username=self.username)
        # handle case where user does not exist
        if not user:
            raise ValueError(f"User {self.username} does not exist")
        user.set_password(self.password)
        user.save()
