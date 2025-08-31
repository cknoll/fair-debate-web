"""
This module enables the command `python manage.py savefixtures --backup` (used in `deploy.py`).
"""

# TODO: evaluate benefit over `python3 manage.py dumpdata --indent 2 base > $backup_path`


from io import StringIO
import re
import json
import os
import time

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings


model_blacklist = ["contenttypes*", "sessions*", r"admin\.logentry",
                   r"auth\.permission"]


class Command(BaseCommand):
    """
    Similar to dumpdata, but with adapted usability:
        - use jsonlint, to generate readable json code,
        - ignore models on the hardcoded blacklist
        - use predefined path
    """
    help = 'Similar to dumpdata, but with adapted usability.'

    def add_arguments(self, parser):
        # Positional arguments
        # parser.add_argument('poll_ids', nargs='+', type=int)

        # Named (optional) arguments
        parser.add_argument(
            '--backup',
            action='store_true',
            help='save the result at settings.BACKUP_PATH and use datetime as filename.',
        )

    def handle(self, *args, **options):
        from ipydex import IPS, activate_ips_on_exception
        activate_ips_on_exception()
        buf = StringIO()
        call_command("dumpdata", stdout=buf)
        buf.seek(0)
        data = json.loads(buf.read())

        blacklist_re = re.compile("|".join(model_blacklist))

        if options.get('backup'):
            opfname = time.strftime(r"%Y-%m-%d__%H-%M-%S_backup_all.json")

            backup_path = settings.BACKUP_PATH
            if not os.path.exists(backup_path):
                os.makedirs(backup_path)
            outputpath = os.path.join(backup_path, opfname)
        else:
            outputpath = time.strftime(r"%Y-%m-%d__%H-%M-%S_all.json")

        keep_data = []
        bad_data = []
        for d in data:
            model = d.get("model")
            if model is None:
                continue
            if blacklist_re.match(model):
                # just for debugging
                bad_data.append(model)
                continue
            else:
                keep_data.append(d)

        # dependency only needed here
        import demjson3
        res = demjson3.encode(keep_data, encoding="utf-8", compactly=False)

        # remove trailing spaces and ensure final linebreak:
        lb = b"\n"  # byte-linebreak
        res2 = lb.join([line.rstrip() for line in res.split(lb)] + [lb])

        # write bytes because we have specified utf8-encoding
        with open(outputpath, "wb") as jfile:
            jfile.write(res2)

        self.stdout.write(f"file written: {outputpath}")
        self.stdout.write(self.style.SUCCESS('Done'))
