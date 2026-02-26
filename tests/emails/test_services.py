import smtplib

import pytest

from emails.constants import EmailType
from emails.services import send_templated_email


@pytest.mark.django_db
def test_send_templated_email_swallows_smtp_error_by_default(monkeypatch):
    def raise_smtp_error(*args, **kwargs):
        raise smtplib.SMTPRecipientsRefused({"test@test.com": (550, b"invalid destination domain")})

    monkeypatch.setattr("emails.services.EmailMultiAlternatives.send", raise_smtp_error)

    result = send_templated_email(
        email_type=EmailType.RESERVATION_RECEIVED,
        recipient="test@test.com",
        context={},
    )

    assert result is False


@pytest.mark.django_db
def test_send_templated_email_can_raise_when_requested(monkeypatch):
    def raise_smtp_error(*args, **kwargs):
        raise smtplib.SMTPRecipientsRefused({"test@test.com": (550, b"invalid destination domain")})

    monkeypatch.setattr("emails.services.EmailMultiAlternatives.send", raise_smtp_error)

    with pytest.raises(smtplib.SMTPRecipientsRefused):
        send_templated_email(
            email_type=EmailType.RESERVATION_RECEIVED,
            recipient="test@test.com",
            context={},
            raise_on_error=True,
        )
