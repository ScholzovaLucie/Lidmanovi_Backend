import textwrap
from pathlib import Path

import pytest
from django.core.management import call_command

from editorial_system.page.models import Page
from editorial_system.page.services import TRANSLATION_MANUALLY_REVIEWED


@pytest.fixture
def locales_dir(tmp_path):
    files = {
        "translations_kontakt.js": """
            export const translations_kontakt = {
              cs: {
                pageTitle: "Kontakt",
                form: { title: "Kontaktujte nas" },
              },
              en: {
                pageTitle: "Contact",
                form: { title: "Contact us" },
              },
              de: {
                pageTitle: "Kontakt",
              },
            };
        """,
        "translations_index.js": """
            export const en = {
              pageTitle: "Home",
            };
            export const cs = {
              pageTitle: "Domu",
            };
        """,
    }
    for name, content in files.items():
        (tmp_path / name).write_text(textwrap.dedent(content), encoding="utf-8")
    return tmp_path


@pytest.mark.django_db
def test_import_frontend_translations_creates_pages_and_i18n(locales_dir):
    call_command("import_frontend_translations", locales_dir=str(locales_dir), source_lang="cs")

    kontakt = Page.objects.get(path="/kontakt", lang="cs")
    index = Page.objects.get(path="/", lang="cs")

    assert kontakt.content_json == {"pageTitle": "Kontakt", "form": {"title": "Kontaktujte nas"}}
    assert kontakt.content_i18n["en"] == {"pageTitle": "Contact", "form": {"title": "Contact us"}}
    assert kontakt.content_i18n["de"] == {"pageTitle": "Kontakt"}
    assert index.content_json == {"pageTitle": "Domu"}
    assert index.content_i18n["en"] == {"pageTitle": "Home"}


@pytest.mark.django_db
def test_import_frontend_translations_respects_if_empty(locales_dir):
    Page.objects.create(
        path="/kontakt",
        lang="cs",
        content_json={"pageTitle": "Existing source"},
        content_i18n={"en": {"pageTitle": "Existing translation"}},
    )

    call_command(
        "import_frontend_translations",
        locales_dir=str(locales_dir),
        source_lang="cs",
        overwrite=True,
        if_empty=True,
    )

    kontakt = Page.objects.get(path="/kontakt", lang="cs")
    assert kontakt.content_json == {"pageTitle": "Existing source"}
    assert kontakt.content_i18n["en"] == {"pageTitle": "Existing translation"}
    assert kontakt.content_i18n["de"] == {"pageTitle": "Kontakt"}


@pytest.mark.django_db
def test_import_frontend_translations_preserves_manual_review_without_overwrite(locales_dir):
    Page.objects.create(
        path="/kontakt",
        lang="cs",
        content_json={"pageTitle": "Kontakt"},
        content_i18n={"en": {"pageTitle": "Manual"}},
        translation_state_i18n={"en": {"state": TRANSLATION_MANUALLY_REVIEWED}},
    )

    call_command("import_frontend_translations", locales_dir=str(locales_dir), source_lang="cs")

    kontakt = Page.objects.get(path="/kontakt", lang="cs")
    assert kontakt.content_i18n["en"] == {"pageTitle": "Manual"}


@pytest.mark.django_db
def test_import_frontend_translations_overwrites_when_requested(locales_dir):
    Page.objects.create(
        path="/kontakt",
        lang="cs",
        content_json={"pageTitle": "Old source"},
        content_i18n={"en": {"pageTitle": "Old translation"}},
        translation_state_i18n={"en": {"state": TRANSLATION_MANUALLY_REVIEWED}},
    )

    call_command(
        "import_frontend_translations",
        locales_dir=str(locales_dir),
        source_lang="cs",
        overwrite=True,
    )

    kontakt = Page.objects.get(path="/kontakt", lang="cs")
    assert kontakt.content_json["pageTitle"] == "Kontakt"
    assert kontakt.content_i18n["en"]["pageTitle"] == "Contact"
