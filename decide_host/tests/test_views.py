# -*- mode: python -*-
import datetime
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse

from decide_host.models import Controller, Component, Event, Trial, Subject


@pytest.mark.django_db
def test_index(client):
    response = client.get(reverse("decide:index"))
    assert response.status_code == 200
