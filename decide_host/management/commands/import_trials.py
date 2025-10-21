# -*- mode: python -*-
"""Import line-delimited records into trial objects using the Django ORM"""

import json

from django.core.management.base import BaseCommand

from decide_host.serializers import TrialSerializer


class Command(BaseCommand):
    help = "import trials from line-delimited JSON (jsonl) files"

    def add_arguments(self, parser):
        parser.add_argument(
            "-n", "--name", help="name of procedure (required)", required=True
        )
        parser.add_argument(
            "-a", "--addr", help="controller name (required)", required=True
        )
        parser.add_argument("files", nargs="+", help="files to import")

    def handle(self, *args, **options):
        for path in options["files"]:
            with open(path) as fp:
                n = 0
                for i, line in enumerate(fp):
                    record = json.loads(line.strip())
                    record["addr"] = options["addr"]
                    record["name"] = options["name"]
                    serializer = TrialSerializer(data=record)
                    if serializer.is_valid():
                        n += 1
                        serializer.save()
                    else:
                        self.stdout.write(
                            f"{path}, record {i} invalid: {serializer.errors}"
                        )
                self.stdout.write(f"{path}: imported {n} record(s)")
