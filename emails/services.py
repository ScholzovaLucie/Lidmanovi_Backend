import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from emails.constants import EmailType

LOGGER = logging.getLogger("emails")

TEMPLATES = {
    EmailType.RESERVATION_RECEIVED: "emails/reservation_received.html",
    EmailType.RESERVATION_APPROVED: "emails/reservation_approved.html",
    EmailType.RESERVATION_REJECTED: "emails/reservation_rejected.html",
    EmailType.GENERIC: "emails/generic_message.html",
}

SUBJECTS = {
    EmailType.RESERVATION_RECEIVED: "Rezervace přijata – Restaurace u Lidmanů",
    EmailType.RESERVATION_APPROVED: "Rezervace potvrzena – Restaurace u Lidmanů",
    EmailType.RESERVATION_REJECTED: "Rezervace zamítnuta – Restaurace u Lidmanů",
    EmailType.GENERIC: "Zpráva z Restaurace u Lidmanů",
}

def send_templated_email(email_type, recipient, context):
    try:
        template = TEMPLATES.get(email_type)

        if not template:
            raise ValueError("Unknown email type")

        html_content = render_to_string(template, context)
        subject = SUBJECTS.get(email_type, "Zpráva z Restaurace u Lidmanů")

        email = EmailMultiAlternatives(
            subject,
            html_content,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        LOGGER.info(
            "Email sent | type=%s | recipient=%s",
            email_type,
            recipient
        )
    except Exception as e:
        LOGGER.error(
            "Email failed | type=%s | recipient=%s | error=%s",
            email_type,
            recipient,
            str(e)
        )
        raise