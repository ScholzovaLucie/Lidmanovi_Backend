import pytest
from rest_framework.test import APIClient

from editorial_system.page.models import Page, PageTranslation
from editorial_system.page.services import TRANSLATION_MANUALLY_REVIEWED


@pytest.mark.django_db
def test_pages_list_can_filter_by_path(auth_client):
    target = Page.objects.create(path="/kontakt", lang="cs", content_json={"title": "Kontakt"})
    Page.objects.create(path="/about", lang="cs", content_json={"title": "O nas"})

    response = auth_client.get("/editorial_system/pages/?path=/kontakt")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == target.id


@pytest.mark.django_db
def test_pages_list_can_filter_by_source_lang(auth_client):
    Page.objects.create(path="/kontakt", lang="cs", content_json={"title": "Kontakt"})
    Page.objects.create(path="/kontakt", lang="en", content_json={"title": "Contact"})

    response = auth_client.get("/editorial_system/pages/?source_lang=en")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["lang"] == "en"


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
    page = Page.objects.create(path="/kontakt", lang="cs", content_json={"title": "Kontakt"})

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

    response = client.get("/editorial_system/pages/?path=/kontakt")

    assert response.status_code == 200
    assert response.data["count"] == 1


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
def test_pages_resolves_translation_from_pagetranslation():
    page = Page.objects.create(path="/kontakt", lang="cs", content_json={"title": "Kontakt"})
    PageTranslation.objects.create(
        page=page,
        lang="en",
        content_json={"title": "Contact"},
        state=TRANSLATION_MANUALLY_REVIEWED,
    )
    client = APIClient()

    response = client.get("/editorial_system/pages/?path=/kontakt&lang=en")

    assert response.status_code == 200
    assert response.data["results"][0]["content_json"]["title"] == "Contact"
    assert response.data["results"][0]["requested_lang"] == "en"
    assert response.data["results"][0]["translation_status"] == TRANSLATION_MANUALLY_REVIEWED


@pytest.mark.django_db
def test_pages_falls_back_to_source_when_translation_missing():
    Page.objects.create(path="/kontakt", lang="cs", content_json={"title": "Kontakt"})
    client = APIClient()

    response = client.get("/editorial_system/pages/?path=/kontakt&lang=en")

    assert response.status_code == 200
    assert response.data["results"][0]["content_json"]["title"] == "Kontakt"
    assert response.data["results"][0]["translation_status"] == "missing"


@pytest.mark.django_db
def test_pages_source_lang_returns_source_of_truth_status():
    Page.objects.create(path="/kontakt", lang="cs", content_json={"title": "Kontakt"})
    client = APIClient()

    response = client.get("/editorial_system/pages/?path=/kontakt&lang=cs")

    assert response.status_code == 200
    assert response.data["results"][0]["translation_status"] == "source_of_truth"


@pytest.mark.django_db
def test_pages_public_response_hides_translations_list():
    page = Page.objects.create(path="/kontakt", lang="cs", content_json={"title": "Kontakt"})
    PageTranslation.objects.create(page=page, lang="en", content_json={"title": "Contact"})
    client = APIClient()

    response = client.get("/editorial_system/pages/?path=/kontakt")

    assert response.status_code == 200
    assert "translations" not in response.data["results"][0]


@pytest.mark.django_db
def test_pages_authenticated_response_includes_translations_list(auth_client):
    page = Page.objects.create(path="/kontakt", lang="cs", content_json={"title": "Kontakt"})
    PageTranslation.objects.create(page=page, lang="en", content_json={"title": "Contact"})

    response = auth_client.get("/editorial_system/pages/?path=/kontakt")

    assert response.status_code == 200
    result = response.data["results"][0]
    assert "translations" in result
    assert len(result["translations"]) == 1
    assert result["translations"][0]["lang"] == "en"


@pytest.mark.django_db
def test_translations_action_get_lists_translations(auth_client):
    page = Page.objects.create(path="/kontakt", lang="cs", content_json={"title": "Kontakt"})
    PageTranslation.objects.create(page=page, lang="en", content_json={"title": "Contact"})
    PageTranslation.objects.create(page=page, lang="de", content_json={"title": "Kontakt DE"})

    response = auth_client.get(f"/editorial_system/pages/{page.id}/translations/")

    assert response.status_code == 200
    assert len(response.data) == 2
    langs = {t["lang"] for t in response.data}
    assert langs == {"en", "de"}


@pytest.mark.django_db
def test_translations_action_patch_creates_translation(auth_client):
    page = Page.objects.create(path="/kontakt", lang="cs", content_json={"title": "Kontakt"})

    response = auth_client.patch(
        f"/editorial_system/pages/{page.id}/translations/",
        {"lang": "en", "content_json": {"title": "Manually reviewed"}},
        format="json",
    )

    assert response.status_code == 200
    translation = PageTranslation.objects.get(page=page, lang="en")
    assert translation.content_json["title"] == "Manually reviewed"
    assert translation.state == TRANSLATION_MANUALLY_REVIEWED


@pytest.mark.django_db
def test_translations_action_patch_updates_existing_translation(auth_client):
    page = Page.objects.create(path="/kontakt", lang="cs", content_json={"title": "Kontakt"})
    PageTranslation.objects.create(page=page, lang="en", content_json={"title": "Old"})

    response = auth_client.patch(
        f"/editorial_system/pages/{page.id}/translations/",
        {"lang": "en", "content_json": {"title": "Updated"}},
        format="json",
    )

    assert response.status_code == 200
    translation = PageTranslation.objects.get(page=page, lang="en")
    assert translation.content_json["title"] == "Updated"
    assert translation.state == TRANSLATION_MANUALLY_REVIEWED
    assert PageTranslation.objects.filter(page=page, lang="en").count() == 1


@pytest.mark.django_db
def test_translations_action_patch_requires_lang_and_content(auth_client):
    page = Page.objects.create(path="/kontakt", lang="cs", content_json={"title": "Kontakt"})

    response = auth_client.patch(
        f"/editorial_system/pages/{page.id}/translations/",
        {"lang": "en"},
        format="json",
    )
    assert response.status_code == 400
    assert "content_json" in response.data


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
    page = Page.objects.create(path="/cenik", lang="cs", content_json={"title": "Cenik"})

    response = auth_client.post(
        f"/editorial_system/pages/{page.id}/translate/",
        {"target_langs": ["en"]},
        format="json",
    )
    assert response.status_code == 404
