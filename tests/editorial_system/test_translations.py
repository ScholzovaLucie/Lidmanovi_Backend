import pytest

from editorial_system.iframe_embed.models import IframeEmbed
from editorial_system.info_box.models import InfoBox


@pytest.mark.django_db
def test_info_box_list_returns_translated_title(auth_client):
    InfoBox.objects.create(
        title="Dulezita informace",
        title_i18n={"en": "Important information"},
        content_json={"a": 1},
    )

    response = auth_client.get("/editorial_system/info_boxes/?lang=en")

    assert response.status_code == 200
    assert response.data[0]["title"] == "Important information"


@pytest.mark.django_db
def test_iframe_list_returns_translated_title_from_accept_language(auth_client):
    IframeEmbed.objects.create(
        title="Mapa",
        title_i18n={"en": "Map"},
        url="https://example.com",
    )

    response = auth_client.get(
        "/editorial_system/iframes/",
        HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9",
    )

    assert response.status_code == 200
    assert response.data[0]["title"] == "Map"
