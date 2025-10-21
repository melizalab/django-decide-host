# -*- mode: python -*-

from django.contrib import admin

from decide_host.models import Component, Controller, Event, Subject, Trial

for model in (Event, Trial, Controller, Component, Subject):
    admin.site.register(model)
