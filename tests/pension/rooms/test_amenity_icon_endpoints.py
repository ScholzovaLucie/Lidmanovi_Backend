import pytest

from pension.amenity.models import AmenityIcon

pytestmark = pytest.mark.usefixtures("mock_emails")


@pytest.mark.django_db
def test_list_amenity_icons_is_seeded_and_unpaginated(auth_client):
    response = auth_client.get("/pension/admin/amenity-icons/")

    assert response.status_code == 200
    assert isinstance(response.data, list)
    keys = [item["key"] for item in response.data]
    assert keys == ["bed", "bathroom", "wifi", "tv", "dog"]


@pytest.mark.django_db
def test_list_amenity_icons_includes_inactive(auth_client):
    AmenityIcon.objects.create(key="parking", label="Parkoviste", order=5, is_active=False)

    response = auth_client.get("/pension/admin/amenity-icons/")

    keys = [item["key"] for item in response.data]
    assert "parking" in keys


@pytest.mark.django_db
def test_create_amenity_icon(auth_client):
    payload = {"key": "parking", "label": "Parkoviste", "order": 5, "is_active": True}

    response = auth_client.post("/pension/admin/amenity-icons/", payload, format="json")

    assert response.status_code == 201, response.data
    assert AmenityIcon.objects.filter(key="parking").exists()


@pytest.mark.django_db
def test_create_amenity_icon_rejects_invalid_key(auth_client):
    payload = {"key": "Invalid Key!", "label": "Bad", "order": 5, "is_active": True}

    response = auth_client.post("/pension/admin/amenity-icons/", payload, format="json")

    assert response.status_code == 400
    assert "key" in response.data


@pytest.mark.django_db
def test_patch_amenity_icon_updates_label_order_and_active(auth_client):
    icon = AmenityIcon.objects.get(key="tv")

    response = auth_client.patch(
        f"/pension/admin/amenity-icons/{icon.id}/",
        {"label": "Chytra televize", "order": 9, "is_active": False},
        format="json",
    )

    assert response.status_code == 200, response.data
    icon.refresh_from_db()
    assert icon.label == "Chytra televize"
    assert icon.order == 9
    assert icon.is_active is False


@pytest.mark.django_db
def test_delete_amenity_icon(auth_client):
    icon = AmenityIcon.objects.create(key="parking", label="Parkoviste", order=5)

    response = auth_client.delete(f"/pension/admin/amenity-icons/{icon.id}/")

    assert response.status_code == 204
    assert not AmenityIcon.objects.filter(id=icon.id).exists()


@pytest.mark.django_db
def test_amenity_icons_require_admin_auth():
    from rest_framework.test import APIClient

    client = APIClient()
    response = client.get("/pension/admin/amenity-icons/")

    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_deactivating_amenity_icon_does_not_break_existing_room(auth_client, room):
    room.amenities = [{"icon": "dog", "text": "Se psem"}]
    room.save()

    dog_icon = AmenityIcon.objects.get(key="dog")
    dog_icon.is_active = False
    dog_icon.save()

    response = auth_client.put(
        f"/pension/admin/rooms/{room.id}/",
        {
            "name": room.name,
            "capacity": room.capacity,
            "description": room.description,
            "price_for_adult": room.price_for_adult,
            "price_for_children": room.price_for_children,
            "is_active": room.is_active,
            "amenities": [{"icon": "dog", "text": "Se psem"}],
        },
        format="json",
    )

    assert response.status_code == 200, response.data
    assert response.data["amenities"] == [{"icon": "dog", "text": "Se psem"}]
