"""
This module enables the command `python manage.py setpassword <username> <password>` (used in `deploy.py`).
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Set password for a user'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('username', type=str, help='Username of the user')
        parser.add_argument('password', type=str, help='New password for the user')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        
        if not username or not password:
            raise CommandError("Username and password are required")
            
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' does not exist")
            
        user.set_password(password)
        user.save()
        
        self.stdout.write(self.style.SUCCESS(f"Successfully set password for user '{username}'"))
