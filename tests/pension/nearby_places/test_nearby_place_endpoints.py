from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from editorial_system.photo.models import Photo, PhotoPlacement
from pension.nearby_place.models import NearbyPlace

pytestmark = pytest.mark.django_db


def create_test_image(name="photo.jpg"):
    content = BytesIO()
    Image.new("RGB", (1, 1), color="white").save(content, format="JPEG")
    return SimpleUploadedFile(name=name, content=content.getvalue(), content_type="image/jpeg")


def test_name_synced_from_name_i18n_cs_on_save():
    place = NearbyPlace.objects.create(
        name="placeholder",
        name_i18n={"cs": "Rozhledna", "en": "Lookout tower"},
        link="https://example.com",
        media_type=NearbyPlace.MediaType.IFRAME,
        media_url="https://example.com/embed",
    )

    assert place.name == "Rozhledna"


def test_name_kept_when_name_i18n_has_no_cs_key():
    place = NearbyPlace.objects.create(
        name="Fallback name",
        name_i18n={"en": "Lookout tower"},
        link="https://example.com",
        media_type=NearbyPlace.MediaType.IFRAME,
        media_url="https://example.com/embed",
    )

    assert place.name == "Fallback name"


def test_create_iframe_place_requires_media_url(auth_client):
    payload = {
        "name_i18n": {"cs": "Aquapark"},
        "link": "https://example.com/aquapark",
        "media_type": "iframe",
    }

    response = auth_client.post("/pension/admin/nearby-places/", payload, format="json")

    assert response.status_code == 400
    assert "media_url" in response.data


def test_create_place_with_long_google_maps_link_succeeds(auth_client):
    # Regression test: `link`/`media_url` used to be plain URLField() with the Django
    # default max_length=200, but real Google Maps place links (the documented use case
    # for `link`) routinely exceed that, causing a Postgres "value too long for type
    # character varying(200)" DataError instead of a clean validation response.
    long_maps_url = (
        "https://www.google.com/maps/place/Pension+-+Restaurace+U+Lidmanu/"
        "@50.497506,16.291047,17z/data=!3m1!4b1!4m6!3m5!"
        "1s0x470e686d9f1caccd:0x5443aff885131f52!8m2!3d50.497506!4d16.2936219"
        "!16s%2Fg%2F1tfr_s_l?entry=ttu&g_ep=EgoyMDI2MDYyNC4wIKXMDSoASAFQAw%3D%3D"
    )
    assert len(long_maps_url) > 200

    payload = {
        "name_i18n": {"cs": "Aquapark"},
        "link": long_maps_url,
        "media_type": "iframe",
        "media_url": long_maps_url,
    }

    response = auth_client.post("/pension/admin/nearby-places/", payload, format="json")

    assert response.status_code == 201
    assert response.data["link"] == long_maps_url


def test_create_place_without_name_field_succeeds(auth_client):
    # Regression test: `name` used to be a required writable field inherited from the
    # model's CharField, but the frontend only ever sends `name_i18n` - it never sends
    # `name`. That made every create/update request fail with a "this field is
    # required" error on `name`. It must be read-only and derived from name_i18n['cs'].
    payload = {
        "name_i18n": {"cs": "Aquapark"},
        "link": "https://example.com/aquapark",
        "media_type": "iframe",
        "media_url": "https://example.com/embed/aquapark",
    }

    response = auth_client.post("/pension/admin/nearby-places/", payload, format="json")

    assert response.status_code == 201
    assert response.data["name"] == "Aquapark"


def test_create_iframe_place_with_media_url_succeeds(auth_client):
    payload = {
        "name_i18n": {"cs": "Aquapark"},
        "link": "https://example.com/aquapark",
        "media_type": "iframe",
        "media_url": "https://example.com/embed/aquapark",
    }

    response = auth_client.post("/pension/admin/nearby-places/", payload, format="json")

    assert response.status_code == 201
    assert response.data["media_url"] == "https://example.com/embed/aquapark"


def test_create_image_place_does_not_require_media_url(auth_client):
    payload = {
        "name_i18n": {"cs": "Zámek"},
        "link": "https://example.com/zamek",
        "media_type": "image",
    }

    response = auth_client.post("/pension/admin/nearby-places/", payload, format="json")

    assert response.status_code == 201
    assert response.data["media_url"] is None


def test_image_place_created_via_api_ignores_submitted_media_url(auth_client):
    payload = {
        "name_i18n": {"cs": "Zámek"},
        "link": "https://example.com/zamek",
        "media_type": "image",
        "media_url": "https://example.com/should-be-ignored.jpg",
    }

    response = auth_client.post("/pension/admin/nearby-places/", payload, format="json")

    assert response.status_code == 201
    place = NearbyPlace.objects.get(id=response.data["id"])
    assert place.media_url == ""


def test_image_place_resolves_media_url_from_photo_placement(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    place = NearbyPlace.objects.create(
        name="Zamek",
        name_i18n={"cs": "Zámek"},
        link="https://example.com/zamek",
        media_type=NearbyPlace.MediaType.IMAGE,
    )
    photo = Photo.objects.create(category="nearby-place", image=create_test_image())
    PhotoPlacement.objects.create(photo=photo, location=f"nearby-place-{place.id}", order=0)

    response = auth_client.get(f"/pension/admin/nearby-places/{place.id}/")

    assert response.status_code == 200
    assert response.data["media_url"]
    assert response.data["media_url"] != ""


def test_image_place_media_url_is_null_without_photo_placement(auth_client):
    place = NearbyPlace.objects.create(
        name="Zamek",
        name_i18n={"cs": "Zámek"},
        link="https://example.com/zamek",
        media_type=NearbyPlace.MediaType.IMAGE,
    )

    response = auth_client.get(f"/pension/admin/nearby-places/{place.id}/")

    assert response.status_code == 200
    assert response.data["media_url"] is None


def test_admin_can_update_via_put(auth_client):
    place = NearbyPlace.objects.create(
        name="Aquapark",
        name_i18n={"cs": "Aquapark"},
        link="https://example.com/aquapark",
        media_type=NearbyPlace.MediaType.IFRAME,
        media_url="https://example.com/embed/aquapark",
    )

    payload = {
        "name_i18n": {"cs": "Aquapark novy"},
        "link": "https://example.com/aquapark",
        "media_type": "iframe",
        "media_url": "https://example.com/embed/aquapark-v2",
        "order": 1,
        "is_active": True,
    }

    response = auth_client.put(f"/pension/admin/nearby-places/{place.id}/", payload, format="json")

    assert response.status_code == 200
    place.refresh_from_db()
    assert place.name == "Aquapark novy"
    assert place.media_url == "https://example.com/embed/aquapark-v2"


def test_public_list_only_returns_active_places(auth_client):
    NearbyPlace.objects.create(
        name="Active",
        name_i18n={"cs": "Active"},
        link="https://example.com/a",
        media_type=NearbyPlace.MediaType.IFRAME,
        media_url="https://example.com/a",
        is_active=True,
    )
    NearbyPlace.objects.create(
        name="Inactive",
        name_i18n={"cs": "Inactive"},
        link="https://example.com/b",
        media_type=NearbyPlace.MediaType.IFRAME,
        media_url="https://example.com/b",
        is_active=False,
    )

    response = APIClient().get("/pension/public/nearby-places/")

    assert response.status_code == 200
    names = [item["name"] for item in response.data]
    assert names == ["Active"]
