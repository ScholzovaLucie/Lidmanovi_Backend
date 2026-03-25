import pytest
from django.core.management import call_command

from editorial_system.photo.models import Photo


@pytest.mark.django_db
def test_sync_photos_from_media_creates_photo_records(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    photos_dir = tmp_path / "editorial" / "photos"
    rooms_dir = photos_dir / "rooms"
    rooms_dir.mkdir(parents=True)
    (rooms_dir / "one.jpg").write_bytes(b"jpg")
    (rooms_dir / "notes.txt").write_text("ignore me", encoding="utf-8")

    gallery_dir = photos_dir / "gallery"
    gallery_dir.mkdir(parents=True)
    (gallery_dir / "two.png").write_bytes(b"png")

    call_command("sync_photos_from_media", photos_dir=str(photos_dir))

    photos = list(Photo.objects.order_by("id").values("category", "image"))
    assert photos == [
        {"category": "gallery", "image": "editorial/photos/gallery/two.png"},
        {"category": "rooms", "image": "editorial/photos/rooms/one.jpg"},
    ]


@pytest.mark.django_db
def test_sync_photos_from_media_does_not_create_duplicates(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    photos_dir = tmp_path / "editorial" / "photos" / "wellness"
    photos_dir.mkdir(parents=True)
    image_path = photos_dir / "spa.webp"
    image_path.write_bytes(b"webp")

    call_command("sync_photos_from_media", photos_dir=str(photos_dir.parent))
    call_command("sync_photos_from_media", photos_dir=str(photos_dir.parent))

    assert Photo.objects.count() == 1
    assert Photo.objects.get().image.name == "editorial/photos/wellness/spa.webp"


@pytest.mark.django_db
def test_sync_photos_from_media_if_empty_skips_when_db_has_records(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    photos_dir = tmp_path / "editorial" / "photos" / "rooms"
    photos_dir.mkdir(parents=True)
    (photos_dir / "one.jpg").write_bytes(b"jpg")

    Photo.objects.create(category="existing", image="editorial/photos/existing/old.jpg")

    call_command("sync_photos_from_media", photos_dir=str(photos_dir.parent), if_empty=True)

    assert Photo.objects.count() == 1
