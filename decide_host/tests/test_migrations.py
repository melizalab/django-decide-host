# -*- mode: python -*-
# These tests run in a subprocess because pytest runs with --no-migrations,
# which hides the migration modules from the test process.
import os
import subprocess
import sys

SETUP = """
import sys
import django
django.setup()
from django.core.management import call_command
"""


def run_django(code, block_modules=()):
    """Runs code in a new python process with Django set up for the test
    settings and an in-memory sqlite database"""
    env = os.environ | {"DJANGO_SETTINGS_MODULE": "decide_host.tests.settings"}
    env.pop("DECIDE_TEST_DB", None)
    blocked = "".join(f"sys.modules[{name!r}] = None\n" for name in block_modules)
    return subprocess.run(
        [sys.executable, "-c", "import sys\n" + blocked + SETUP + code],
        env=env,
        capture_output=True,
        text=True,
    )


def test_migrations_run_on_sqlite_without_psycopg():
    result = run_django(
        'call_command("migrate", verbosity=0)',
        block_modules=("psycopg", "psycopg2"),
    )
    assert result.returncode == 0, result.stderr


def test_no_missing_migrations():
    result = run_django(
        'call_command("makemigrations", "decide_host", "--check", "--dry-run")'
    )
    assert result.returncode == 0, result.stdout + result.stderr
