import pytest
from rest_framework.test import APIClient

from editorial_system.page.models import Page
from editorial_system.page.services import TRANSLATION_MANUALLY_REVIEWED


@pytest.mark.django_db
def test_pages_list_can_filter_by_path_and_lang(auth_client):
    target_page = Page.objects.create(
        path="/kontakt",
        lang="cs",
        content_json={"title": "Kontakt"},
    )
    Page.objects.create(path="/kontakt", lang="en", content_json={"title": "Contact"})
    Page.objects.create(path="/about", lang="cs", content_json={"title": "O nas"})

    response = auth_client.get("/editorial_system/pages/?path=/kontakt&lang=cs")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["id"] == target_page.id
    assert response.data["results"][0]["path"] == "/kontakt"
    assert response.data["results"][0]["lang"] == "cs"


@pytest.mark.django_db
def test_pages_upsert_put_creates_when_missing(auth_client):
    response = auth_client.put(
        "/editorial_system/pages/upsert/",
        {"path": "/kontakt", "lang": "cs", "content_json": {"title": "Kontakt"}},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["path"] == "/kontakt"
    assert response.data["lang"] == "cs"
    assert response.data["content_json"]["title"] == "Kontakt"
    assert Page.objects.filter(path="/kontakt", lang="cs").exists()


@pytest.mark.django_db
def test_pages_upsert_patch_updates_existing(auth_client):
    page = Page.objects.create(
        path="/kontakt",
        lang="cs",
        content_json={"title": "Kontakt"},
    )

    response = auth_client.patch(
        "/editorial_system/pages/upsert/",
        {"path": "/kontakt", "lang": "cs", "content_json": {"title": "Kontakt novy"}},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["id"] == page.id
    assert response.data["content_json"]["title"] == "Kontakt novy"

    page.refresh_from_db()
    assert page.content_json["title"] == "Kontakt novy"


@pytest.mark.django_db
def test_pages_upsert_requires_path_and_lang(auth_client):
    response = auth_client.patch(
        "/editorial_system/pages/upsert/",
        {"content_json": {"title": "Kontakt"}},
        format="json",
    )

    assert response.status_code == 400
    assert "path" in response.data


@pytest.mark.django_db
def test_pages_list_is_public_for_unauthenticated_user():
    Page.objects.create(path="/kontakt", lang="cs", content_json={"title": "Kontakt"})
    client = APIClient()

    response = client.get("/editorial_system/pages/?path=/kontakt&lang=cs")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_pages_create_requires_authentication():
    client = APIClient()

    response = client.post(
        "/editorial_system/pages/",
        {"path": "/kontakt", "lang": "cs", "content_json": {"title": "Kontakt"}},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_pages_upsert_does_not_generate_i18n_content(auth_client):
    response = auth_client.put(
        "/editorial_system/pages/upsert/",
        {"path": "/kontakt", "lang": "cs", "content_json": {"title": "Kontakt"}},
        format="json",
    )
    assert response.status_code == 201

    page = Page.objects.get(path="/kontakt", lang="cs")
    assert page.content_i18n == {}
    assert page.translation_state_i18n == {}


@pytest.mark.django_db
def test_pages_can_return_translated_content_for_requested_lang_without_separate_row():
    Page.objects.create(
        path="/kontakt",
        lang="cs",
        content_json={"title": "Kontakt"},
        content_i18n={"en": {"title": "Contact"}},
        translation_state_i18n={"en": {"state": TRANSLATION_MANUALLY_REVIEWED}},
    )
    client = APIClient()

    response = client.get("/editorial_system/pages/?path=/kontakt&lang=en")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["content_json"]["title"] == "Contact"
    assert response.data["results"][0]["requested_lang"] == "en"
    assert response.data["results"][0]["translation_status"] == TRANSLATION_MANUALLY_REVIEWED


@pytest.mark.django_db
def test_pages_manual_translation_override_is_preserved_on_source_update(auth_client):
    create_response = auth_client.put(
        "/editorial_system/pages/upsert/",
        {"path": "/kontakt", "lang": "cs", "content_json": {"title": "Kontakt"}},
        format="json",
    )
    page_id = create_response.data["id"]

    manual_response = auth_client.patch(
        f"/editorial_system/pages/{page_id}/translations/",
        {"lang": "en", "content_json": {"title": "Manually reviewed"}},
        format="json",
    )
    assert manual_response.status_code == 200

    update_response = auth_client.patch(
        "/editorial_system/pages/upsert/",
        {"path": "/kontakt", "lang": "cs", "content_json": {"title": "Kontakt novy"}},
        format="json",
    )
    assert update_response.status_code == 200

    page = Page.objects.get(id=page_id)
    assert page.content_i18n["en"]["title"] == "Manually reviewed"
    assert page.translation_state_i18n["en"]["state"] == TRANSLATION_MANUALLY_REVIEWED


@pytest.mark.django_db
def test_pages_translate_all_endpoint_is_not_available(auth_client):
    response = auth_client.post(
        "/editorial_system/pages/translate-all/",
        {"target_langs": ["en"]},
        format="json",
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_pages_translate_endpoint_is_not_available(auth_client):
    page = Page.objects.create(
        path="/cenik",
        lang="cs",
        content_json={"title": "Cenik"},
    )

    response = auth_client.post(
        f"/editorial_system/pages/{page.id}/translate/",
        {"target_langs": ["en"]},
        format="json",
    )

    assert response.status_code == 404
