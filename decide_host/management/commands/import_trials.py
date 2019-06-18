# -*- coding: utf-8 -*-
# -*- mode: python -*-
""" Import line-delimited records into trial objects using the Django ORM """

from django.core.management.base import BaseCommand, CommandError
from decide_host.models import Trial
from decide_host.serializers import TrialSerializer

import json


class Command(BaseCommand):
    help = "import trials from line-delimited JSON (jsonl) files"

    def add_arguments(self, parser):
        parser.add_argument("-n", "--name", help="name of procedure (required)", required=True)
        parser.add_argument("-a", "--addr", help="controller name (required)", required=True)
        parser.add_argument('files', nargs="+", help="files to import")

    def handle(self, *args, **options):
        for path in options['files']:
            with open(path, "rU") as fp:
                n = 0
                for i, line in enumerate(fp):
                    record = json.loads(line.strip())
                    record['addr'] = options['addr']
                    record['name'] = options['name']
                    serializer = TrialSerializer(data=record)
                    if serializer.is_valid():
                        n += 1
                        serializer.save()
                    else:
                        self.stdout.write("%s, record %d invalid: %s" % (path, i, serializer.errors))
                self.stdout.write("%s: imported %d record(s)" % (path, n))
