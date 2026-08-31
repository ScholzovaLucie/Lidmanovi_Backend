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
    EmailType.RESERVATION_PAYD: "emails/reservation_payd.html",
    EmailType.RESERVATION_DONE: "emails/reservation_done.html",
    EmailType.VOUCHER_ORDER_RECEIVED: "emails/voucher_order_received.html",
    EmailType.VOUCHER_ORDER_CONFIRMED: "emails/voucher_order_confirmed.html",
    EmailType.VOUCHER_ORDER_SENT: "emails/voucher_order_sent.html",
    EmailType.VOUCHER_ORDER_CANCELLED: "emails/voucher_order_cancelled.html",
    EmailType.ADMIN_NEW_RESERVATION: "emails/admin_new_reservation.html",
    EmailType.ADMIN_NEW_VOUCHER_ORDER: "emails/admin_new_voucher_order.html",
    EmailType.GENERIC: "emails/generic_message.html",
}

SUBJECTS = {
    EmailType.RESERVATION_RECEIVED: "Rezervace přijata – Restaurace u Lidmanů",
    EmailType.RESERVATION_APPROVED: "Rezervace potvrzena – Restaurace u Lidmanů",
    EmailType.RESERVATION_REJECTED: "Rezervace zamítnuta – Restaurace u Lidmanů",
    EmailType.RESERVATION_PAYD: "Rezervace zaplacena – Restaurace u Lidmanů",
    EmailType.RESERVATION_DONE: "Rezervace dokončena – Restaurace u Lidmanů",
    EmailType.VOUCHER_ORDER_RECEIVED: "Objednávka poukazu přijata – Restaurace u Lidmanů",
    EmailType.VOUCHER_ORDER_CONFIRMED: "Objednávka poukazu potvrzena – Restaurace u Lidmanů",
    EmailType.VOUCHER_ORDER_SENT: "Poukaz odeslán – Restaurace u Lidmanů",
    EmailType.VOUCHER_ORDER_CANCELLED: "Objednávka poukazu zrušena – Restaurace u Lidmanů",
    EmailType.ADMIN_NEW_RESERVATION: "Nová rezervace – Restaurace u Lidmanů",
    EmailType.ADMIN_NEW_VOUCHER_ORDER: "Nová objednávka poukazu – Restaurace u Lidmanů",
    EmailType.GENERIC: "Zpráva z Restaurace u Lidmanů",
}

def send_templated_email(email_type, recipient, context, raise_on_error=False):
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
        sent_count = email.send(fail_silently=not raise_on_error)

        if sent_count:
            LOGGER.info(
                "Email sent | type=%s | recipient=%s",
                email_type,
                recipient
            )
            return True

        LOGGER.warning(
            "Email not sent | type=%s | recipient=%s",
            email_type,
            recipient
        )
        return False
    except Exception as e:
        LOGGER.error(
            "Email failed | type=%s | recipient=%s | error=%s",
            email_type,
            recipient,
            str(e)
        )
        if raise_on_error:
            raise
        return False
