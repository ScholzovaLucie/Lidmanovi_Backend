import textwrap
from pathlib import Path

import pytest
from django.core.management import call_command

from editorial_system.page.models import Page, PageTranslation
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
                pageTitle: "Kontakt DE",
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
def test_import_creates_page_and_pagetranslation_records(locales_dir):
    call_command("import_frontend_translations", locales_dir=str(locales_dir), source_lang="cs")

    kontakt = Page.objects.get(path="/kontakt", lang="cs")
    index = Page.objects.get(path="/", lang="cs")

    assert kontakt.content_json == {"pageTitle": "Kontakt", "form": {"title": "Kontaktujte nas"}}
    assert index.content_json == {"pageTitle": "Domu"}

    en = PageTranslation.objects.get(page=kontakt, lang="en")
    de = PageTranslation.objects.get(page=kontakt, lang="de")
    assert en.content_json == {"pageTitle": "Contact", "form": {"title": "Contact us"}}
    assert de.content_json == {"pageTitle": "Kontakt DE"}

    index_en = PageTranslation.objects.get(page=index, lang="en")
    assert index_en.content_json == {"pageTitle": "Home"}


@pytest.mark.django_db
def test_import_respects_if_empty_for_existing_source(locales_dir):
    page = Page.objects.create(
        path="/kontakt",
        lang="cs",
        content_json={"pageTitle": "Existing source"},
    )
    PageTranslation.objects.create(page=page, lang="en", content_json={"pageTitle": "Existing EN"})

    call_command(
        "import_frontend_translations",
        locales_dir=str(locales_dir),
        source_lang="cs",
        overwrite=True,
        if_empty=True,
    )

    page.refresh_from_db()
    assert page.content_json["pageTitle"] == "Existing source"

    en = PageTranslation.objects.get(page=page, lang="en")
    assert en.content_json["pageTitle"] == "Existing EN"

    de = PageTranslation.objects.get(page=page, lang="de")
    assert de.content_json["pageTitle"] == "Kontakt DE"


@pytest.mark.django_db
def test_import_preserves_manually_reviewed_without_overwrite(locales_dir):
    page = Page.objects.create(path="/kontakt", lang="cs", content_json={"pageTitle": "Kontakt"})
    PageTranslation.objects.create(
        page=page,
        lang="en",
        content_json={"pageTitle": "Manual EN"},
        state=TRANSLATION_MANUALLY_REVIEWED,
    )

    call_command("import_frontend_translations", locales_dir=str(locales_dir), source_lang="cs")

    en = PageTranslation.objects.get(page=page, lang="en")
    assert en.content_json["pageTitle"] == "Manual EN"


@pytest.mark.django_db
def test_import_overwrites_manually_reviewed_when_overwrite_flag_set(locales_dir):
    page = Page.objects.create(path="/kontakt", lang="cs", content_json={"pageTitle": "Old"})
    PageTranslation.objects.create(
        page=page,
        lang="en",
        content_json={"pageTitle": "Old EN"},
        state=TRANSLATION_MANUALLY_REVIEWED,
    )

    call_command(
        "import_frontend_translations",
        locales_dir=str(locales_dir),
        source_lang="cs",
        overwrite=True,
    )

    page.refresh_from_db()
    assert page.content_json["pageTitle"] == "Kontakt"
    en = PageTranslation.objects.get(page=page, lang="en")
    assert en.content_json["pageTitle"] == "Contact"


@pytest.mark.django_db
def test_import_does_not_create_duplicate_translations(locales_dir):
    call_command("import_frontend_translations", locales_dir=str(locales_dir), source_lang="cs")
    call_command("import_frontend_translations", locales_dir=str(locales_dir), source_lang="cs")

    kontakt = Page.objects.get(path="/kontakt", lang="cs")
    assert PageTranslation.objects.filter(page=kontakt, lang="en").count() == 1
    assert PageTranslation.objects.filter(page=kontakt, lang="de").count() == 1