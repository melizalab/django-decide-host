# -*- coding: utf-8 -*-
# -*- mode: python -*-
from __future__ import unicode_literals

from django.contrib import admin
from decide_host.models import Event, Trial, Controller, Component, Subject

for model in (Event, Trial, Controller, Component, Subject):
    admin.site.register(model)
