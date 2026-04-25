from io import StringIO
import re
import json
import os
import time

import fair_debate_md as fdmd

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    """
    t.b.d
    """
    help = "t.b.d."

    def add_arguments(self, parser):
        parser.add_argument(
            "--unit-test-mode",
            action="store_true",
            help="create the content repos in the path expected by unittests",
        )

    def handle(self, *args, **options):

        if options.get("unit_test_mode"):
            target_dir = settings.REPO_HOST_DIR_FOR_TESTS
        else:
            target_dir = settings.REPO_HOST_DIR
        fdmd.unpack_repos(target_dir)
