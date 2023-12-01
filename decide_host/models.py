# -*- coding: utf-8 -*-
# -*- mode: python -*-
from __future__ import unicode_literals

from django.db.models import JSONField, Count, Max, Q
from django.utils import timezone
from django.db import models


class EventManager(models.Manager):
    def with_names(self):
        return self.select_related("addr", "name")


class Event(models.Model):
    """An event is any state change in a connected controller"""

    id = models.AutoField(primary_key=True)
    addr = models.ForeignKey(
        "Controller",
        on_delete=models.PROTECT,
        help_text="the controller that generated the event",
    )
    name = models.ForeignKey(
        "Component", on_delete=models.PROTECT, help_text="the name of the component"
    )
    time = models.DateTimeField(db_index=True)
    data = JSONField()
    objects = EventManager()

    def __str__(self):
        return "%s:%s @ %s" % (self.addr, self.name, self.time.isoformat())

    class Meta:
        unique_together = ("addr", "name", "time")
        indexes = [models.Index(fields=["addr", "-time"], name="addr_time_desc_idx")]
        ordering = ("-time",)


class TrialManager(models.Manager):
    def with_names(self):
        return self.select_related("addr", "subject", "name")


class Trial(models.Model):
    """A trial is one set of events in an experimental paradigm"""

    id = models.AutoField(primary_key=True)
    addr = models.ForeignKey(
        "Controller", on_delete=models.PROTECT, help_text="the controller for the trial"
    )
    name = models.ForeignKey(
        "Component",
        on_delete=models.PROTECT,
        help_text="the experiment paradigm (e.g., shape)",
    )
    subject = models.ForeignKey(
        "Subject", on_delete=models.PROTECT, help_text="the experimental subject"
    )
    time = models.DateTimeField(db_index=True)
    data = JSONField()
    objects = TrialManager()

    def __str__(self):
        return "%s:%s @ %s" % (self.addr, self.subject, self.time.isoformat())

    class Meta:
        unique_together = ("name", "subject", "time")
        indexes = [
            models.Index(fields=["subject", "-time"], name="subject_time_desc_idx")
        ]
        ordering = ("-time",)


class ControllerManager(models.Manager):
    def with_counts(self):
        return self.annotate(
            n_events=Count("event"), last_event_time=Max("event__time")
        )


class Controller(models.Model):
    """Represents a controller connected to this host"""

    id = models.AutoField(primary_key=True)
    name = models.SlugField(max_length=32, unique=True)
    objects = ControllerManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)


class Component(models.Model):
    """Represents a component in a controller"""

    # the main reason for having this as a separate model rather than a string
    # field is to reduce data size and enhance indexing
    id = models.AutoField(primary_key=True)
    name = models.SlugField(max_length=32, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)


class SubjectManager(models.Manager):
    def with_counts(self):
        today_start = timezone.localtime(timezone.now()).replace(
            hour=0, minute=0, second=0
        )
        return self.annotate(
            n_trials=Count("trial"),
            last_trial_time=Max("trial__time"),
            n_trials_today=Count("trial", filter=Q(trial__time__gte=today_start)),
        )


class Subject(models.Model):
    """Represents an experimental subject"""

    id = models.AutoField(primary_key=True)
    name = models.SlugField(max_length=36, unique=True)
    objects = SubjectManager()

    def n_trials_today(self):
        today_start = timezone.localtime(timezone.now()).replace(
            hour=0, minute=0, second=0
        )
        today_end = today_start.replace(hour=23, minute=59, second=59)
        return self.trial_set.filter(time__gte=today_start, time__lte=today_end).count()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)
