import pytest
from rest_framework.test import APIClient

from pension.room.models import Room


@pytest.mark.django_db
def test_public_room_list_returns_translation_from_lang_query():
    Room.objects.create(
        name="Pokoj Komfort",
        name_i18n={"en": "Comfort Room"},
        description="Cesky popis",
        description_i18n={"en": "English description"},
        capacity=3,
        price_for_adult=1000,
        price_for_children=500,
    )

    client = APIClient()
    response = client.get("/pension/public/rooms/?lang=en")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["name"] == "Comfort Room"
    assert response.data["results"][0]["description"] == "English description"
    assert "name_i18n" not in response.data["results"][0]
    assert "description_i18n" not in response.data["results"][0]


@pytest.mark.django_db
def test_public_room_list_uses_accept_language_when_lang_query_missing():
    Room.objects.create(
        name="Rodinny pokoj",
        name_i18n={"de": "Familienzimmer"},
        description="Zakladni popis",
        description_i18n={"de": "Grundbeschreibung"},
        capacity=4,
        price_for_adult=1200,
        price_for_children=600,
    )

    client = APIClient()
    response = client.get("/pension/public/rooms/", HTTP_ACCEPT_LANGUAGE="de-DE,de;q=0.9,en;q=0.8")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["name"] == "Familienzimmer"
    assert response.data["results"][0]["description"] == "Grundbeschreibung"
