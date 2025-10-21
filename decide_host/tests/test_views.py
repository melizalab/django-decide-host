# -*- mode: python -*-
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_index(client):
    response = client.get(reverse("decide:index"))
    assert response.status_code == 200
