import pytest

from pension.guest.models import Guest


@pytest.mark.django_db
def test_guest_list_filters_by_fulltext_query_string(auth_client):
    matching_by_name = Guest.objects.create(
        first_name="Lucie",
        last_name="Novakova",
        email="lucie@example.com",
        phone="+420777111222",
        country="CZ",
        note="VIP guest",
    )
    matching_by_phone = Guest.objects.create(
        first_name="Pavel",
        last_name="Svoboda",
        email="pavel@example.com",
        phone="+420777333444",
        country="CZ",
        note="Regular guest",
    )
    Guest.objects.create(
        first_name="Jana",
        last_name="Kralova",
        email="jana@example.com",
        phone="+420777555666",
        country="Germany",
        note="Contains Lucie in note only",
    )

    response_name = auth_client.get("/pension/admin/guests/", {"queryString": "lucie"})

    assert response_name.status_code == 200
    assert response_name.data["count"] == 1
    assert [item["id"] for item in response_name.data["results"]] == [matching_by_name.id]

    response_phone = auth_client.get("/pension/admin/guests/", {"queryString": "333444"})

    assert response_phone.status_code == 200
    assert response_phone.data["count"] == 1
    assert [item["id"] for item in response_phone.data["results"]] == [matching_by_phone.id]


@pytest.mark.django_db
def test_guest_list_query_string_searches_only_name_surname_phone_and_email(auth_client):
    Guest.objects.create(
        first_name="Alena",
        last_name="Nova",
        email="alena@example.com",
        phone="+420777123123",
        country="Austria",
        note="Special keyword hidden here",
    )

    response_country = auth_client.get("/pension/admin/guests/", {"queryString": "Austria"})
    response_note = auth_client.get("/pension/admin/guests/", {"queryString": "keyword"})

    assert response_country.status_code == 200
    assert response_country.data["count"] == 0
    assert response_note.status_code == 200
    assert response_note.data["count"] == 0
