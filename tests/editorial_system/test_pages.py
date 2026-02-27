import pytest
from rest_framework.test import APIClient

from editorial_system.page.models import Page


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
    assert len(response.data) == 1
    assert response.data[0]["id"] == target_page.id
    assert response.data[0]["path"] == "/kontakt"
    assert response.data[0]["lang"] == "cs"


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
    assert len(response.data) == 1


@pytest.mark.django_db
def test_pages_create_requires_authentication():
    client = APIClient()

    response = client.post(
        "/editorial_system/pages/",
        {"path": "/kontakt", "lang": "cs", "content_json": {"title": "Kontakt"}},
        format="json",
    )

    assert response.status_code == 401
