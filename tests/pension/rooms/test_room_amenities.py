import pytest

from pension.room.models import Room

pytestmark = pytest.mark.usefixtures("mock_emails")

VALID_AMENITIES = [
    {"icon": "bed", "text": ""},
    {"icon": "tv", "text": "Smart TV"},
    {"icon": "dog", "text": "Se psem"},
]


@pytest.mark.django_db
def test_public_room_list_includes_amenities(auth_client, room):
    room.amenities = VALID_AMENITIES
    room.save()

    response = auth_client.get("/pension/public/rooms/")

    assert response.status_code == 200
    body = response.data["results"] if "results" in response.data else response.data
    room_data = next(r for r in body if r["id"] == room.id)
    assert room_data["amenities"] == VALID_AMENITIES


@pytest.mark.django_db
def test_admin_create_room_with_amenities(auth_client):
    payload = {
        "name": "Amenity room",
        "capacity": 3,
        "description": "Room with amenities",
        "price_for_adult": 1000,
        "price_for_children": 500,
        "is_active": True,
        "amenities": VALID_AMENITIES,
    }

    response = auth_client.post("/pension/admin/rooms/", payload, format="json")

    assert response.status_code == 201, response.data
    assert response.data["amenities"] == VALID_AMENITIES
    created = Room.objects.get(id=response.data["id"])
    assert created.amenities == VALID_AMENITIES


@pytest.mark.django_db
def test_admin_update_room_with_amenities(auth_client, room):
    response = auth_client.put(
        f"/pension/admin/rooms/{room.id}/",
        {
            "name": room.name,
            "capacity": room.capacity,
            "description": room.description,
            "price_for_adult": room.price_for_adult,
            "price_for_children": room.price_for_children,
            "is_active": room.is_active,
            "amenities": VALID_AMENITIES,
        },
        format="json",
    )

    assert response.status_code == 200, response.data
    assert response.data["amenities"] == VALID_AMENITIES
    room.refresh_from_db()
    assert room.amenities == VALID_AMENITIES


@pytest.mark.django_db
def test_admin_update_room_rejects_invalid_icon(auth_client, room):
    response = auth_client.put(
        f"/pension/admin/rooms/{room.id}/",
        {
            "name": room.name,
            "capacity": room.capacity,
            "description": room.description,
            "price_for_adult": room.price_for_adult,
            "price_for_children": room.price_for_children,
            "is_active": room.is_active,
            "amenities": [{"icon": "parking", "text": ""}],
        },
        format="json",
    )

    assert response.status_code == 400
    assert "amenities" in response.data


@pytest.mark.django_db
def test_admin_update_room_rejects_non_string_text(auth_client, room):
    response = auth_client.put(
        f"/pension/admin/rooms/{room.id}/",
        {
            "name": room.name,
            "capacity": room.capacity,
            "description": room.description,
            "price_for_adult": room.price_for_adult,
            "price_for_children": room.price_for_children,
            "is_active": room.is_active,
            "amenities": [{"icon": "tv", "text": 5}],
        },
        format="json",
    )

    assert response.status_code == 400
    assert "amenities" in response.data


@pytest.mark.django_db
def test_room_amenities_default_is_empty_list():
    room = Room.objects.create(
        name="Default amenities room",
        capacity=2,
        price_for_adult=1000,
        price_for_children=0,
    )
    assert room.amenities == []