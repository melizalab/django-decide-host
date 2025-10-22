# -*- mode: python -*-
import pytest
from django.utils import timezone

from decide_host.models import Component, Controller, Event, Subject, Trial
from decide_host.serializers import EventSerializer, TrialSerializer


@pytest.fixture
def component(db):
    return Component.objects.create(name="peck_keys")


@pytest.fixture
def controller(db):
    return Controller.objects.create(name="beagle-1")


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="ruby_230")


@pytest.mark.django_db
def test_event_data_flattening(component, controller):
    timestamp = timezone.now()
    event = Event.objects.create(
        name=component,
        addr=controller,
        time=timestamp,
        data={"state": {"peck_left": True}},
    )
    serializer = EventSerializer(event)
    data = serializer.data
    assert data["name"] == component.name
    assert data["addr"] == controller.name
    assert "data" not in data, "data field was not flattened"
    assert data["state"] == {"peck_left": True}, "flattened data does not match"


@pytest.mark.django_db
def test_event_data_unflattening():
    timestamp = timezone.now()
    data = {
        "name": "peck_keys",
        "addr": "beagle-1",
        "time": timestamp.timestamp(),
        "state": {"peck_left": True},
    }
    serializer = EventSerializer(data=data)
    assert serializer.is_valid()
    event = serializer.save()
    assert event.name.name == data["name"]
    assert event.addr.name == data["addr"]
    assert event.time == timestamp
    assert event.data == {"state": data["state"]}


@pytest.mark.django_db
def test_trial_data_flattening(component, controller, subject):
    timestamp = timezone.now()
    trial = Trial.objects.create(
        name=component,
        addr=controller,
        subject=subject,
        time=timestamp,
        data={"experiment": "test", "stimulus": "stim-1"},
    )
    serializer = TrialSerializer(trial)
    data = serializer.data
    assert data["name"] == component.name
    assert data["addr"] == controller.name
    assert data["subject"] == subject.name
    assert "data" not in data, "data field was not flattened"
    assert data["experiment"] == "test", "flattened data does not match"


@pytest.mark.django_db
def test_trial_data_unflattening():
    timestamp = timezone.now()
    data = {
        "name": "peck_keys",
        "addr": "beagle-1",
        "subject": "ruby_230",
        "time": timestamp.timestamp(),
        "experiment": "test",
        "stimulus": "stim-1",
    }
    serializer = TrialSerializer(data=data)
    assert serializer.is_valid()
    trial = serializer.save()
    assert trial.name.name == data["name"]
    assert trial.addr.name == data["addr"]
    assert trial.subject.name == data["subject"]
    assert trial.time == timestamp
    assert trial.data == {
        "experiment": data["experiment"],
        "stimulus": data["stimulus"],
    }


@pytest.mark.django_db
def test_trial_creation_with_existing_objects(component, controller, subject):
    timestamp = timezone.now()
    data = {
        "name": component.name,
        "addr": controller.name,
        "subject": subject.name,
        "time": timestamp.timestamp(),
        "experiment": "test",
        "stimulus": "stim-1",
    }
    serializer = TrialSerializer(data=data)
    assert serializer.is_valid()
    trial = serializer.save()
    assert trial.name == component
    assert trial.addr == controller
    assert trial.subject == subject
    assert trial.time == timestamp
