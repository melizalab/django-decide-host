# -*- mode: python -*-
import datetime
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from decide_host.models import Controller, Component, Event, Trial, Subject


@pytest.fixture
def sentinel_user():
    return get_user_model().objects.get_or_create(username="deleted")[0]


@pytest.mark.django_db
def test_controller_event_counts():
    controller = Controller.objects.create(name="beagle-1")
    component = Component.objects.create(name="peck-keys")
    timestamp = timezone.now()
    Event.objects.create(
        name=component,
        addr=controller,
        time=timestamp,
        data={"state": {"peck_left": False}},
    )

    controllers = Controller.objects.with_counts()
    assert controllers.count() == 1
    assert controllers.first().n_events == 1
    assert controllers.first().last_event_time == timestamp


@pytest.mark.django_db
def test_subject_trial_counts():
    subject = Subject.objects.create(name="ruby_1")
    component = Component.objects.create(name="gng")
    controller = Controller.objects.create(name="beagle-1")
    timestamp_today = timezone.now()
    timestamp_yesterday = timestamp_today - datetime.timedelta(days=1)
    Trial.objects.create(
        name=component,
        addr=controller,
        subject=subject,
        time=timestamp_yesterday,
        data={"experiment": "test", "stimulus": "stim-1"},
    )
    Trial.objects.create(
        name=component,
        addr=controller,
        subject=subject,
        time=timestamp_today,
        data={"experiment": "test", "stimulus": "stim-2"},
    )

    assert subject.n_trials_today() == 1

    subjects = Subject.objects.with_counts()
    assert subjects.count() == 1
    subj = subjects.first()
    assert subj.n_trials == 2
    assert subj.last_trial_time == timestamp_today
    assert subj.n_trials_today == 1
