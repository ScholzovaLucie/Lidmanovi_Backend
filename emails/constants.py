class EmailType:
    RESERVATION_RECEIVED = "reservation_received"
    RESERVATION_APPROVED = "reservation_approved"
    RESERVATION_REJECTED = "reservation_rejected"
    RESERVATION_PAYD = "reservation_payd"
    RESERVATION_DONE = "reservation_done"
    GENERIC = "generic"

    CHOICES = [
        (RESERVATION_RECEIVED, "Reservation received"),
        (RESERVATION_APPROVED, "Reservation approved"),
        (RESERVATION_REJECTED, "Reservation rejected"),
        (RESERVATION_PAYD, "Reservation payd"),
        (RESERVATION_DONE, "Reservation done"),
        (GENERIC, "Generic message"),
    ]