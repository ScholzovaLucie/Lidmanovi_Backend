class EmailType:
    RESERVATION_RECEIVED = "reservation_received"
    RESERVATION_APPROVED = "reservation_approved"
    RESERVATION_REJECTED = "reservation_rejected"
    RESERVATION_PAYD = "reservation_payd"
    RESERVATION_DONE = "reservation_done"
    VOUCHER_ORDER_RECEIVED = "voucher_order_received"
    VOUCHER_ORDER_CONFIRMED = "voucher_order_confirmed"
    VOUCHER_ORDER_SENT = "voucher_order_sent"
    VOUCHER_ORDER_CANCELLED = "voucher_order_cancelled"
    ADMIN_NEW_RESERVATION = "admin_new_reservation"
    ADMIN_NEW_VOUCHER_ORDER = "admin_new_voucher_order"
    GENERIC = "generic"

    CHOICES = [
        (RESERVATION_RECEIVED, "Reservation received"),
        (RESERVATION_APPROVED, "Reservation approved"),
        (RESERVATION_REJECTED, "Reservation rejected"),
        (RESERVATION_PAYD, "Reservation payd"),
        (RESERVATION_DONE, "Reservation done"),
        (VOUCHER_ORDER_RECEIVED, "Voucher order received"),
        (VOUCHER_ORDER_CONFIRMED, "Voucher order confirmed"),
        (VOUCHER_ORDER_SENT, "Voucher order sent"),
        (VOUCHER_ORDER_CANCELLED, "Voucher order cancelled"),
        (ADMIN_NEW_RESERVATION, "Admin notification: new reservation"),
        (ADMIN_NEW_VOUCHER_ORDER, "Admin notification: new voucher order"),
        (GENERIC, "Generic message"),
    ]