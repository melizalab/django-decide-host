# -*- mode: python -*-
"""Combine duplicate subject objects using the Django ORM"""

from django.core.management.base import BaseCommand

from decide_host.models import Subject


class Command(BaseCommand):
    help = "combine duplicate subjects using the Django ORM"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="don't commit the result to the database",
        )
        parser.add_argument("to_keep", help="name of the subject that will be kept")
        parser.add_argument(
            "to_combine",
            nargs="+",
            help="names of subjects to merge with the subject being kept",
        )

    def handle(self, *args, **options):
        try:
            dest_subj = Subject.objects.get(name=options["to_keep"])
        except Subject.DoesNotExist:
            self.stdout.write(f"- no such subject {options['to_keep']}, aborting")
            return
        for subj_name in options["to_combine"]:
            try:
                src_subj = Subject.objects.get(name=subj_name)
            except Subject.DoesNotExist:
                self.stdout.write(f"- no such subject {subj_name}, skipping")
                continue
            n_trials = src_subj.trial_set.count()
            self.stdout.write(
                f"- reassigning {n_trials} trial(s) from {src_subj.name} to {dest_subj.name}"
            )
            if not options["dry_run"]:
                src_subj.trial_set.update(subject=dest_subj)
                assert src_subj.trial_set.count() == 0
                src_subj.delete()
                self.stdout.write(f"- deleted {src_subj.name}")
