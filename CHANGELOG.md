# Changelog

All notable changes to this project are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.4.0] - unreleased

### Added

- Trial and event lists can be streamed as newline-delimited JSON. Send
  `Accept: application/x-ndjson` (or add `format=ndjson` to the query) to get
  all matching records in one unpaginated response. Records are identical to
  the paginated JSON. Requests with other `Accept` headers, including `*/*`,
  still get paginated JSON.
- `page_size` query parameter sets the number of records per page, up to
  10000. The default is still set by `REST_FRAMEWORK["PAGE_SIZE"]`.
- Support for Django 6.0 and 6.1.

### Changed

- Exact-match `data__` filters also match JSON booleans, numbers, and `null`.
  For example, `data__correct=True` (or `true`) now matches records where
  `correct` is `true`, and `data__trial=3` matches `3` as well as `"3"`.
  Previously these filters compared against strings and matched nothing.
- Requires Python 3.11 or later, djangorestframework 3.18 or later, and
  django-filter 25.1 or later. Dependencies now have upper version bounds.
- Documented that comparison lookups on `data__` fields (e.g.
  `data__rtime__lt=500`) compare values as strings and don't work for numeric
  fields.

### Removed

- Support for Python 3.10.

### Fixed

- Migrations failed on SQLite unless psycopg was installed, because the
  initial migration imported `django.contrib.postgres`. The migration now uses
  `models.JSONField`, which creates the same `jsonb` column on PostgreSQL, so
  existing databases are unaffected.

### Deployment notes

- No new migrations.
- Streaming responses keep a worker busy for their whole duration. Check the
  WSGI server's request timeout (e.g. gunicorn `--timeout`). If PostgreSQL is
  behind pgbouncer in transaction pooling mode, set
  `DISABLE_SERVER_SIDE_CURSORS = True` in the database settings.

### Development

- Tests run against an in-memory SQLite database by default. Set
  `DECIDE_TEST_DB=postgres` to test against PostgreSQL, as CI does.
- The PostgreSQL driver for testing is now psycopg 3, in the optional
  `postgres` dependency group (`uv sync --group postgres`).
- Tests run in UTC, and CI covers Python 3.11–3.14 and Django 5.2 and 6.1.

[0.4.0]: https://github.com/melizalab/django-decide-host/compare/v0.3.11...v0.4.0
