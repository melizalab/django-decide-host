# -*- coding: utf-8 -*-
# -*- mode: python -*-
from __future__ import unicode_literals

import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_text
from django.utils.timezone import make_aware
from rest_framework import serializers
from decide_host.models import Controller, Component, Event, Subject, Trial

# ideally, I'd like to flatten the JSON so that all the data fields are at the
# top level. This simplifies the representation


class CreatableSlugRelatedField(serializers.SlugRelatedField):

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get_or_create(**{self.slug_field: data})[0]
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.slug_field, value=smart_text(data))
        except (TypeError, ValueError):
            self.fail('invalid')


class MicroDateTimeField(serializers.DateTimeField):
    """Class to handle floating point timestamps"""

    def to_internal_value(self, data):
        if isinstance(data, float):
            return make_aware(datetime.datetime.fromtimestamp(data))
        if isinstance(data, int):
            return make_aware(datetime.datetime.fromtimestamp(data * 1e-6))
        else:
            return super(MicroDateTimeField, self).to_internal_value(data)


class JSONFlattenMixin(object):
    """Flatens the specified related objects in this representation"""
    def to_representation(self, obj):
        """Move fields from data to top-level"""
        try:
            flatten_field = self.Meta.flatten
        except AttributeError:
            raise AssertionError(
                'Class {serializer_class} missing "Meta.flatten" attribute'.format(
                    serializer_class=self.__class__.__name__))
        repr = super(JSONFlattenMixin, self).to_representation(obj)
        data = repr.pop(flatten_field)
        for key in data:
            repr[key] = data[key]
        return repr

    def to_internal_value(self, data):
        try:
            flatten_field = self.Meta.flatten
        except AttributeError:
            raise AssertionError(
                'Class {serializer_class} missing "Meta.flatten" attribute'.format(
                    serializer_class=self.__class__.__name__))
        dd = {key: data[key] for key in data if key not in self.Meta.fields}
        for key in dd:
            data.pop(key)
        internal = super().to_internal_value(data)
        try:
            internal[flatten_field].update(dd)
        except KeyError:
            internal[flatten_field] = dd
        return internal


class ControllerSerializer(serializers.ModelSerializer):
    last_event_time = serializers.DateTimeField(read_only=True, source="last_event.time")

    class Meta:
        model = Controller
        fields = ("name", "last_event_time")


class SubjectSerializer(serializers.ModelSerializer):
    last_trial_time = serializers.DateTimeField(read_only=True, source="last_trial.time")
    n_trials_today = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subject
        fields = ("name", "last_trial_time", "n_trials_today")


class EventSerializer(JSONFlattenMixin, serializers.ModelSerializer):
    addr = CreatableSlugRelatedField(queryset=Controller.objects.all(),
                                     slug_field="name")
    name = CreatableSlugRelatedField(queryset=Component.objects.all(),
                                     slug_field="name")
    time = MicroDateTimeField()
    data = serializers.JSONField(default=dict)

    class Meta:
        model = Event
        fields = ("addr", "name", "time", "data")
        flatten = "data"


class TrialSerializer(JSONFlattenMixin, serializers.ModelSerializer):
    addr = CreatableSlugRelatedField(queryset=Controller.objects.all(),
                                     slug_field="name")
    name = CreatableSlugRelatedField(queryset=Component.objects.all(),
                                     slug_field="name")
    subject = CreatableSlugRelatedField(queryset=Subject.objects.all(),
                                        slug_field="name")
    time = MicroDateTimeField()
    data = serializers.JSONField(default=dict)

    class Meta:
        model = Trial
        fields = ("addr", "name", "subject", "time", "data")
        flatten = "data"
