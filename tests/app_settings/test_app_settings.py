import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from pension.app_setting.models import AppSetting


@pytest.mark.django_db
def test_public_get_returns_default_settings():
    response = APIClient().get("/app-settings/")

    assert response.status_code == 200
    assert response.data == {"languageSwitcher.enabled": True}


@pytest.mark.django_db
def test_public_get_returns_all_settings():
    AppSetting.objects.create(key="site.name", value="U Lidmanu")
    AppSetting.objects.create(key="feature.flags", value={"gallery": True})

    response = APIClient().get("/app-settings/")

    assert response.status_code == 200
    assert response.data == {
        "feature.flags": {"gallery": True},
        "languageSwitcher.enabled": True,
        "site.name": "U Lidmanu",
    }


@pytest.mark.django_db
def test_post_requires_administrator():
    response = APIClient().post(
        "/app-settings/",
        {"key": "languageSwitcher.enabled", "value": False},
        format="json",
    )

    assert response.status_code == 401

    user = User.objects.create_user(username="user", password="password")
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post(
        "/app-settings/",
        {"key": "languageSwitcher.enabled", "value": False},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    "value",
    [False, "text", 42, {"nested": ["value", 1]}, ["item", True], None],
)
def test_admin_post_creates_settings_with_json_values(auth_client, value):
    response = auth_client.post(
        "/app-settings/",
        {"key": "test.value", "value": value},
        format="json",
    )

    assert response.status_code == 200
    assert response.data == {"key": "test.value", "value": value}
    assert AppSetting.objects.get(key="test.value").value == value


@pytest.mark.django_db
def test_admin_post_replaces_existing_setting(auth_client):
    response = auth_client.post(
        "/app-settings/",
        {"key": "languageSwitcher.enabled", "value": False},
        format="json",
    )

    assert response.status_code == 200
    assert AppSetting.objects.filter(key="languageSwitcher.enabled").count() == 1
    assert AppSetting.objects.get(key="languageSwitcher.enabled").value is False
