import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient
from pension.room.models import Room
from pension.guest.models import Guest
from unittest.mock import Mock

@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="admin",
        password="admin123",
        is_staff=True
    )


@pytest.fixture
def auth_client(staff_user):
    client = APIClient()
    client.force_authenticate(user=staff_user)
    return client


@pytest.fixture
def room():
    return Room.objects.create(
        id=1,
        name="Test room",
        capacity=4,
        max_children=2,
        max_adults=2,
        description="Test room",
        price_for_adult=1000,
        price_for_children=500,
    )


@pytest.fixture
def guest():
    return Guest.objects.create(
        email="test@test.cz",
        first_name="John",
        last_name="Doe"
    )


@pytest.fixture
def staff_client(staff_user):
    client = APIClient()
    client.force_authenticate(user=staff_user)
    return client


@pytest.fixture(autouse=True)
def _reset_throttle_cache():
    # DRF throttling stores request counters in Django's cache, which otherwise persists
    # across tests in the same process and makes unrelated tests fail with 429.
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def mock_emails(monkeypatch):
    mocked_sender = Mock()
    monkeypatch.setattr("pension.reservation.views.send_templated_email", mocked_sender)
    monkeypatch.setattr("emails.views.send_templated_email", mocked_sender)
    return mocked_sender
