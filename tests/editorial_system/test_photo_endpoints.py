from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from editorial_system.photo.models import Photo


pytestmark = pytest.mark.django_db


@pytest.fixture
def public_client():
    return APIClient()


def create_test_image(name="photo.jpg"):
    content = BytesIO()
    Image.new("RGB", (1, 1), color="white").save(content, format="JPEG")
    return SimpleUploadedFile(name=name, content=content.getvalue(), content_type="image/jpeg")


def test_list_photos_returns_ids_urls_and_categories(public_client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    photo = Photo.objects.create(category="wellness", image=create_test_image())

    response = public_client.get("/editorial_system/photos/")
    payload = response.data.get("results", response.data)

    assert response.status_code == 200
    assert len(payload) == 1
    assert payload[0]["id"] == photo.id
    assert payload[0]["category"] == "wellness"
    assert payload[0]["url"].endswith(".jpg")
    assert payload[0]["variants"]["card"] == payload[0]["url"]


def test_by_ids_returns_only_requested_photos_in_same_order(public_client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    first = Photo.objects.create(category="rooms", image=create_test_image("first.jpg"))
    Photo.objects.create(category="wellness", image=create_test_image("ignored.jpg"))
    third = Photo.objects.create(category="garden", image=create_test_image("third.jpg"))

    response = public_client.post(
        "/editorial_system/photos/by-ids/",
        {"ids": [third.id, first.id]},
        format="json",
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [third.id, first.id]


def test_by_category_returns_matching_photos(public_client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    Photo.objects.create(category="rooms", image=create_test_image("room.jpg"))
    Photo.objects.create(category="wellness", image=create_test_image("spa.jpg"))

    response = public_client.get("/editorial_system/photos/by-category/?category=ROOMS")

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["category"] == "rooms"


def test_authenticated_user_can_upload_single_photo(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    response = auth_client.post(
        "/editorial_system/photos/",
        {"category": "rooms", "image": create_test_image()},
        format="multipart",
    )

    assert response.status_code == 201
    assert response.data["category"] == "rooms"
    assert Photo.objects.count() == 1


def test_authenticated_user_can_update_alt_text(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    photo = Photo.objects.create(category="rooms", image=create_test_image())

    response = auth_client.patch(
        f"/editorial_system/photos/{photo.id}/",
        {"alt_text_i18n": {"cs": "Pokoj s výhledem", "en": "Room with a view"}},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["alt_text_i18n"] == {"cs": "Pokoj s výhledem", "en": "Room with a view"}

    photo.refresh_from_db()
    assert photo.alt_text_i18n == {"cs": "Pokoj s výhledem", "en": "Room with a view"}


def test_unauthenticated_user_cannot_update_alt_text(public_client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    photo = Photo.objects.create(category="rooms", image=create_test_image())

    response = public_client.patch(
        f"/editorial_system/photos/{photo.id}/",
        {"alt_text_i18n": {"cs": "Pokoj s výhledem"}},
        format="json",
    )

    assert response.status_code == 401


def test_authenticated_user_can_upload_multiple_photos(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    response = auth_client.post(
        "/editorial_system/photos/",
        {
            "category": "gallery",
            "images": [
                create_test_image("one.jpg"),
                create_test_image("two.jpg"),
            ],
        },
        format="multipart",
    )

    assert response.status_code == 201
    assert len(response.data) == 2
    assert Photo.objects.count() == 2
