from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from editorial_system.info_box.models import InfoBox


@pytest.mark.django_db
def test_public_info_boxes_list_returns_only_currently_active_items():
    now = timezone.now()
    active = InfoBox.objects.create(
        title_i18n={"cs": "Aktualni"},
        content_json={"message": "Zobrazuje se"},
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(hours=1),
    )
    InfoBox.objects.create(
        title_i18n={"cs": "Budouci"},
        content_json={"message": "Nezobrazuje se"},
        starts_at=now + timedelta(hours=1),
        ends_at=now + timedelta(hours=2),
    )
    InfoBox.objects.create(
        title_i18n={"cs": "Expirovany"},
        content_json={"message": "Nezobrazuje se"},
        starts_at=now - timedelta(hours=2),
        ends_at=now - timedelta(minutes=1),
    )

    client = APIClient()
    response = client.get("/editorial_system/public/info-boxes/")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["id"] == active.id
    assert response.data["results"][0]["title"] == "Aktualni"


@pytest.mark.django_db
def test_public_info_boxes_list_includes_open_ended_active_items():
    now = timezone.now()
    without_start = InfoBox.objects.create(
        title_i18n={"cs": "Bez zacatku"},
        content_json={"message": "Aktivni"},
        ends_at=now + timedelta(hours=1),
    )
    without_end = InfoBox.objects.create(
        title_i18n={"cs": "Bez konce"},
        content_json={"message": "Aktivni"},
        starts_at=now - timedelta(hours=1),
    )
    always_active = InfoBox.objects.create(
        title_i18n={"cs": "Vzdy aktivni"},
        content_json={"message": "Aktivni"},
    )

    client = APIClient()
    response = client.get("/editorial_system/public/info-boxes/")

    assert response.status_code == 200
    assert response.data["count"] == 3
    returned_ids = [item["id"] for item in response.data["results"]]
    assert returned_ids == [without_start.id, without_end.id, always_active.id]


@pytest.mark.django_db
def test_private_info_boxes_list_requires_authentication():
    InfoBox.objects.create(title_i18n={"cs": "Interni"}, content_json={"message": "Only admin"})
    client = APIClient()

    response = client.get("/editorial_system/info-boxes/")

    assert response.status_code == 401
