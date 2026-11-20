# -*- mode: python -*-
import datetime
import json

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


NDJSON = "application/x-ndjson"


def ndjson_records(response):
    assert response.streaming
    assert response["Content-Type"] == NDJSON
    body = b"".join(response.streaming_content).decode()
    assert body.endswith("\n")
    return [json.loads(line) for line in body.splitlines()]


@pytest.fixture
def mixed_trials(component, controller, subject):
    other = Subject.objects.create(name="other_subj")
    t0 = timezone.now()
    return Trial.objects.bulk_create(
        Trial(
            name=component,
            addr=controller,
            subject=subject if i % 2 else other,
            time=t0 - datetime.timedelta(seconds=i, microseconds=i),
            data={
                "trial": i,
                "correct": i % 3 == 0,
                "result": "feed" if i % 3 == 0 else "none",
                "stim": "é",
                "nested": [1, {}],
            },
        )
        for i in range(7)
    )


@pytest.mark.parametrize(
    "params",
    [{}, {"subject": "ruby_230"}, {"data__result": "feed"}, {"nocomment": True}],
)
def test_trial_list_ndjson_matches_json(client, mixed_trials, params):
    expected = client.get(
        reverse("decide:trial-list"), params, HTTP_ACCEPT="application/json"
    ).json()
    assert len(expected) > 0
    response = client.get(reverse("decide:trial-list"), params, HTTP_ACCEPT=NDJSON)
    assert response.status_code == 200
    assert ndjson_records(response) == expected


def test_trial_list_ndjson_is_not_paginated(client, trials, default_page_size):
    response = client.get(reverse("decide:trial-list"), HTTP_ACCEPT=NDJSON)
    assert response.status_code == 200
    assert "Link" not in response.headers
    assert [d["trial"] for d in ndjson_records(response)] == [0, 1, 2, 3, 4]


def test_trial_list_ndjson_batches(client, trials, monkeypatch):
    from decide_host.views import TrialList

    monkeypatch.setattr(TrialList, "stream_chunk_size", 2)
    response = client.get(reverse("decide:trial-list"), HTTP_ACCEPT=NDJSON)
    chunks = list(response.streaming_content)
    assert len(chunks) == 3
    lines = b"".join(chunks).decode().splitlines()
    assert [json.loads(line)["trial"] for line in lines] == [0, 1, 2, 3, 4]


def test_trial_list_ndjson_format_param(client, trials):
    response = client.get(reverse("decide:trial-list"), {"format": "ndjson"})
    assert response.status_code == 200
    assert len(ndjson_records(response)) == 5


def test_trial_list_ndjson_empty(client, db):
    response = client.get(reverse("decide:trial-list"), HTTP_ACCEPT=NDJSON)
    assert response.status_code == 200
    assert b"".join(response.streaming_content) == b""


def test_trial_list_wildcard_accept_is_paginated_json(
    client, trials, default_page_size
):
    response = client.get(reverse("decide:trial-list"), HTTP_ACCEPT="*/*")
    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    assert len(response.json()) == 2
    assert "Accept" in response["Vary"]


def test_subject_trial_list_ndjson(client, mixed_trials, subject):
    url = reverse("decide:subject-trial-list", args=[subject.name])
    expected = client.get(url, HTTP_ACCEPT="application/json").json()
    response = client.get(url, HTTP_ACCEPT=NDJSON)
    assert response.status_code == 200
    assert ndjson_records(response) == expected


def test_subject_trial_list_ndjson_unknown_subject(client, db):
    url = reverse("decide:subject-trial-list", args=["nobody"])
    response = client.get(url, HTTP_ACCEPT=NDJSON)
    assert response.status_code == 404
    assert not response.streaming
    assert json.loads(response.content) == {
        "detail": "No Subject matches the given query."
    }


@pytest.fixture
def events(component, controller):
    t0 = timezone.now()
    return Event.objects.bulk_create(
        Event(
            name=component,
            addr=controller,
            time=t0 - datetime.timedelta(seconds=i),
            data={"i": i, "state": "up" if i % 2 else "down"},
        )
        for i in range(5)
    )


@pytest.mark.parametrize("params", [{}, {"data__state": "up"}])
def test_event_list_ndjson_matches_json(client, events, params):
    expected = client.get(
        reverse("decide:event-list"), params, HTTP_ACCEPT="application/json"
    ).json()
    response = client.get(reverse("decide:event-list"), params, HTTP_ACCEPT=NDJSON)
    assert response.status_code == 200
    assert ndjson_records(response) == expected


def test_controller_event_list_ndjson(client, events, controller):
    url = reverse("decide:controller-event-list", args=[controller.name])
    expected = client.get(url, HTTP_ACCEPT="application/json").json()
    response = client.get(url, HTTP_ACCEPT=NDJSON)
    assert response.status_code == 200
    assert ndjson_records(response) == expected


@pytest.fixture
def typed_trials(component, controller, subject):
    t0 = timezone.now()
    values = [
        {"correct": True, "trial": 3, "rtime": 0.5, "stim": "123", "comment": None},
        {"correct": False, "trial": 4, "rtime": 1.5, "stim": "abc", "comment": "x"},
    ]
    return Trial.objects.bulk_create(
        Trial(
            name=component,
            addr=controller,
            subject=subject,
            time=t0 - datetime.timedelta(seconds=i),
            data=data,
        )
        for i, data in enumerate(values)
    )


@pytest.mark.parametrize(
    "params,expected_trials",
    [
        ({"data__correct": "True"}, [3]),
        ({"data__correct": "true"}, [3]),
        ({"data__correct": "False"}, [4]),
        ({"data__correct": "false"}, [4]),
        ({"data__trial": "3"}, [3]),
        ({"data__trial__exact": "4"}, [4]),
        ({"data__rtime": "1.5"}, [4]),
        ({"data__stim": "123"}, [3]),  # numeric-looking strings still match
        ({"data__stim": "abc"}, [4]),
        ({"data__comment": "null"}, [3]),
        ({"data__stim__icontains": "AB"}, [4]),  # other lookups are unchanged
        ({"data__correct": "true", "data__trial": "4"}, []),
    ],
)
def test_trial_list_data_filter_types(client, typed_trials, params, expected_trials):
    response = client.get(reverse("decide:trial-list"), params)
    assert response.status_code == 200
    assert [d["trial"] for d in response.data] == expected_trials


@pytest.mark.parametrize(
    "value,expected",
    [
        ("true", True),
        ("True", True),
        ("false", False),
        ("False", False),
        ("null", None),
        ("3", 3),
        ("-1.5", -1.5),
    ],
)
def test_parse_json_scalar(value, expected):
    from decide_host.views import parse_json_scalar

    assert parse_json_scalar(value) == expected
    assert type(parse_json_scalar(value)) is type(expected)


@pytest.mark.parametrize(
    "value", ["abc", "", '"abc"', "[1]", '{"a": 1}', "NaN", "Infinity", "TRUE"]
)
def test_parse_json_scalar_rejects(value):
    from decide_host.views import _NOT_SCALAR, parse_json_scalar

    assert parse_json_scalar(value) is _NOT_SCALAR
