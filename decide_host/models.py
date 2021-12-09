# -*- coding: utf-8 -*-
# -*- mode: python -*-
from __future__ import unicode_literals

from django.db.models import JSONField
from django.utils import timezone
from django.db import models

# Create your models here.

class Event(models.Model):
    """ An event is any state change in a connected controller """
    id = models.AutoField(primary_key=True)
    addr = models.ForeignKey("Controller",
                             on_delete=models.PROTECT,
                             help_text="the controller that generated the event")
    name = models.ForeignKey("Component",
                             on_delete=models.PROTECT,
                             help_text="the name of the component")
    time = models.DateTimeField()
    data = JSONField()

    def __str__(self):
        return "%s:%s @ %s" % (self.addr, self.name, self.time.isoformat())

    class Meta:
        unique_together = ("addr", "name", "time")
        ordering = ("-time",)



class Trial(models.Model):
    """ A trial is one set of events in an experimental paradigm """
    id = models.AutoField(primary_key=True)
    addr = models.ForeignKey("Controller",
                             on_delete=models.PROTECT,
                             help_text="the controller for the trial")
    name = models.ForeignKey("Component",
                             on_delete=models.PROTECT,
                             help_text="the experiment paradigm (e.g., shape)")
    subject = models.ForeignKey("Subject",
                                on_delete=models.PROTECT,
                                help_text="the experimental subject")
    time = models.DateTimeField()
    data = JSONField()

    def __str__(self):
        return "%s:%s @ %s" % (self.addr, self.subject, self.time.isoformat())

    class Meta:
        unique_together = ("addr", "name", "subject", "time")
        ordering = ("-time",)



class Controller(models.Model):
    """ Represents a controller connected to this host """
    id = models.AutoField(primary_key=True)
    name = models.SlugField(max_length=32, unique=True)

    def last_event(self):
        return self.event_set.first()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)




class Component(models.Model):
    """ Represents a component in a controller """
    # the main reason for having this as a separate model rather than a string
    # field is to reduce data size and enhance indexing
    id = models.AutoField(primary_key=True)
    name = models.SlugField(max_length=32, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)



class Subject(models.Model):
    """ Represents an experimental subject """
    id = models.AutoField(primary_key=True)
    name = models.SlugField(max_length=128, unique=True)

    def last_trial(self):
        return self.trial_set.first()

    def n_trials_today(self):
        today_start = timezone.localtime(timezone.now()).replace(hour=0, minute=0, second=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)
        return self.trial_set.filter(time__gte=today_start, time__lte=today_end).count()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)
