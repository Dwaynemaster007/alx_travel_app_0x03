import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task
def send_booking_confirmation_email(booking_id, customer_email=None):
    """Email the guest a confirmation for a newly created booking."""
    from .models import Booking

    try:
        booking = Booking.objects.select_related("listing", "user").get(pk=booking_id)
    except Booking.DoesNotExist:
        logger.warning("Booking %s no longer exists; no confirmation sent.", booking_id)
        return "booking not found"

    recipient = customer_email or booking.user.email
    if not recipient:
        logger.info("Booking %s: guest has no email address; no confirmation sent.", booking_id)
        return "no recipient"

    subject = f"Booking Confirmation #{booking.id}"
    message = (
        f"Hi {booking.user.get_username()},\n\n"
        f"Your booking at {booking.listing.title} ({booking.listing.location}) "
        f"has been received.\n\n"
        f"Check-in:  {booking.check_in}\n"
        f"Check-out: {booking.check_out}\n"
        f"Nights:    {booking.nights}\n"
        f"Total:     {booking.total_price}\n\n"
        "Thank you for booking with ALX Travel App."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
    return f"sent to {recipient}"
