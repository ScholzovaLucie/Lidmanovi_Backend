import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from pension.room.models import Room
from pension.guest.models import Guest

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
        capacity=4,
        max_children=2,
        max_adults=2,
        price=1000,
        description="Test room",
    )


@pytest.fixture
def guest():
    return Guest.objects.create(
        email="test@test.cz",
        document_number="123",
        first_name="John",
        last_name="Doe"
    )


@pytest.fixture
def staff_client(staff_user):
    client = APIClient()
    client.force_authenticate(user=staff_user)
    return client

