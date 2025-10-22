# -*- mode: python -*-
import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from decide_host.models import Component, Controller, Event, Subject, Trial


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
def test_index(client):
    response = client.get(reverse("decide:index"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_info_at_desired_location(client):
    response = client.get("/decide/api/info/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_event_list_at_desired_location(client):
    response = client.get("/decide/api/events/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_event_list_filter(client, component, controller):
    time_midpoint = timezone.now() - datetime.timedelta(days=3)
    timestamp_1 = time_midpoint - datetime.timedelta(days=1)
    timestamp_2 = time_midpoint + datetime.timedelta(days=1)
    event_1 = Event.objects.create(
        name=component, addr=controller, time=timestamp_1, data={"state": "up"}
    )
    event_2 = Event.objects.create(
        name=component,
        addr=controller,
        time=timestamp_2,
        data={"state": "down"},
    )

    response = client.get(reverse("decide:event-list"))
    assert response.status_code == 200
    assert len(response.data) == 2

    response = client.get(reverse("decide:event-list"), {"data__state": "up"})
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["state"] == "up"

    response = client.get(
        reverse("decide:event-list"), {"date_after": timestamp_1.strftime("%Y-%m-%d")}
    )
    assert response.status_code == 200
    assert len(response.data) == 2, "expected date_after to be inclusive but it was not"

    response = client.get(
        reverse("decide:event-list"), {"date_before": timestamp_2.strftime("%Y-%m-%d")}
    )
    assert response.status_code == 200
    assert len(response.data) == 2, (
        "expected date_before to be inclusive but it was not"
    )

    response = client.get(
        reverse("decide:event-list"),
        {"date_before": time_midpoint.strftime("%Y-%m-%d")},
    )
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["state"] == event_1.data["state"]

    response = client.get(
        reverse("decide:event-list"), {"date_after": time_midpoint.strftime("%Y-%m-%d")}
    )
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["state"] == event_2.data["state"]


@pytest.mark.django_db
def test_trial_list_at_desired_location(client):
    response = client.get("/decide/api/trials/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_trial_list_filter(client, component, controller, subject):
    time_midpoint = timezone.now() - datetime.timedelta(days=3)
    timestamp_1 = time_midpoint - datetime.timedelta(days=1)
    timestamp_2 = time_midpoint + datetime.timedelta(days=1)
    trial_1 = Trial.objects.create(
        name=component,
        addr=controller,
        subject=subject,
        time=timestamp_1,
        data={"state": "up"},
    )
    trial_2 = Trial.objects.create(
        name=component,
        addr=controller,
        subject=subject,
        time=timestamp_2,
        data={"state": "down"},
    )

    response = client.get(reverse("decide:trial-list"))
    assert response.status_code == 200
    assert len(response.data) == 2

    response = client.get(reverse("decide:trial-list"), {"data__state": "up"})
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["state"] == "up"

    response = client.get(
        reverse("decide:trial-list"), {"date_after": timestamp_1.strftime("%Y-%m-%d")}
    )
    assert response.status_code == 200
    assert len(response.data) == 2, "expected date_after to be inclusive but it was not"

    response = client.get(
        reverse("decide:trial-list"), {"date_before": timestamp_2.strftime("%Y-%m-%d")}
    )
    assert response.status_code == 200
    assert len(response.data) == 2, (
        "expected date_before to be inclusive but it was not"
    )

    response = client.get(
        reverse("decide:trial-list"),
        {"date_before": time_midpoint.strftime("%Y-%m-%d")},
    )
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["state"] == trial_1.data["state"]

    response = client.get(
        reverse("decide:trial-list"), {"date_after": time_midpoint.strftime("%Y-%m-%d")}
    )
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["state"] == trial_2.data["state"]
