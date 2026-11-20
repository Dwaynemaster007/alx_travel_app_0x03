from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .models import Booking


@shared_task
def send_booking_confirmation_email(booking_id, customer_email):
    """Email the guest a summary of their booking."""
    booking = Booking.objects.select_related('listing').get(pk=booking_id)
    send_mail(
        subject=f'Booking Confirmation #{booking.id}',
        message=(
            f'Thanks for booking {booking.listing.title} in {booking.listing.location}.\n'
            f'Check-in: {booking.check_in}\nCheck-out: {booking.check_out}\n'
            f'Total: {booking.total_price}'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[customer_email],
    )
    return f'Confirmation sent to {customer_email}'
