# -*- mode: python -*-
try:
    from importlib.metadata import version

    __version__ = version("django-decide-host")
except ImportError:
    # If package is not installed (e.g. during development)
    __version__ = "unknown"
api_version = "1.1"
