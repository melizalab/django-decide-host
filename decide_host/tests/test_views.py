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


@pytest.fixture
def trials(component, controller, subject):
    t0 = timezone.now()
    return Trial.objects.bulk_create(
        Trial(
            name=component,
            addr=controller,
            subject=subject,
            time=t0 - datetime.timedelta(seconds=i),
            data={"trial": i},
        )
        for i in range(5)
    )


@pytest.fixture
def default_page_size(monkeypatch):
    from decide_host.views import LinkHeaderPaginationByTimestamp

    monkeypatch.setattr(LinkHeaderPaginationByTimestamp, "page_size", 2)
    return LinkHeaderPaginationByTimestamp


def test_trial_list_default_page_size(client, trials, default_page_size):
    response = client.get(reverse("decide:trial-list"))
    assert response.status_code == 200
    assert len(response.data) == 2
    assert 'rel="next"' in response.headers["Link"]


def test_trial_list_client_page_size(client, trials, default_page_size):
    response = client.get(reverse("decide:trial-list"), {"page_size": 3})
    assert response.status_code == 200
    assert [d["trial"] for d in response.data] == [0, 1, 2]
    links = response.headers["Link"]
    assert 'rel="next"' in links
    assert "page_size=3" in links

    response = client.get(reverse("decide:trial-list"), {"page_size": 3, "page": 2})
    assert [d["trial"] for d in response.data] == [3, 4]
    assert 'rel="next"' not in response.headers["Link"]


def test_trial_list_page_size_capped(client, trials, default_page_size, monkeypatch):
    monkeypatch.setattr(default_page_size, "max_page_size", 4)
    response = client.get(reverse("decide:trial-list"), {"page_size": 1000})
    assert response.status_code == 200
    assert len(response.data) == 4


def test_subject_trial_list_client_page_size(
    client, trials, subject, default_page_size
):
    response = client.get(
        reverse("decide:subject-trial-list", args=[subject.name]), {"page_size": 5}
    )
    assert response.status_code == 200
    assert len(response.data) == 5
    assert "Link" not in response.headers


def test_event_list_client_page_size(client, component, controller, default_page_size):
    t0 = timezone.now()
    Event.objects.bulk_create(
        Event(
            name=component,
            addr=controller,
            time=t0 - datetime.timedelta(seconds=i),
            data={"i": i},
        )
        for i in range(5)
    )
    response = client.get(reverse("decide:event-list"), {"page_size": 4})
    assert response.status_code == 200
    assert len(response.data) == 4
