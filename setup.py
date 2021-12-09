# -*- coding: utf-8 -*-
# -*- mode: python -*-
import os
import sys
from setuptools import setup
if sys.hexversion < 0x03060000:
    raise RuntimeError("Python 3.6 or higher required")

from decide_host import __version__

VERSION = __version__
cls_txt = """
Development Status :: 3 - Alpha
Framework :: Django
Intended Audience :: Science/Research
License :: OSI Approved :: GNU General Public License (GPL)
Programming Language :: Python
Topic :: Scientific/Engineering
Topic :: Internet :: WWW/HTTP
Topic :: Internet :: WWW/HTTP :: Dynamic Content
"""

setup(
    name="django-decide-host",
    version=VERSION,
    description="A Django-based host for the decide operant control system",
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    classifiers=[x for x in cls_txt.split("\n") if x],
    author='C Daniel Meliza',
    maintainer='C Daniel Meliza',
    url="https://github.com/melizalab/django-decide-host",
    packages=['decide_host'],
    include_package_data=True,
)
