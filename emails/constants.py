class EmailType:
    RESERVATION_RECEIVED = "reservation_received"
    RESERVATION_APPROVED = "reservation_approved"
    RESERVATION_REJECTED = "reservation_rejected"
    GENERIC = "generic"

    CHOICES = [
        (RESERVATION_RECEIVED, "Reservation received"),
        (RESERVATION_APPROVED, "Reservation approved"),
        (RESERVATION_REJECTED, "Reservation rejected"),
        (GENERIC, "Generic message"),
    ]