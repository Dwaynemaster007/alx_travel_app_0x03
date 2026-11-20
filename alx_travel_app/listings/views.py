import logging

from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from .models import Booking, Listing, Review
from .serializers import BookingSerializer, ListingSerializer, ReviewSerializer
from .tasks import send_booking_confirmation_email

logger = logging.getLogger(__name__)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Anyone can read; only the listing's host can change it."""

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.host == request.user


class ListingViewSet(viewsets.ModelViewSet):
    """Browse listings; signed-in users can create them and edit their own."""
    queryset = Listing.objects.select_related('host')
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)


class BookingViewSet(viewsets.ModelViewSet):
    """Users see and manage their own bookings; staff see all of them."""
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # drf-yasg builds the schema without a user
            return Booking.objects.none()
        user = self.request.user
        queryset = Booking.objects.select_related('listing', 'user')
        return queryset if user.is_staff else queryset.filter(user=user)

    def perform_create(self, serializer):
        # Booking.save() works out total_price from the nightly rate
        booking = serializer.save(user=self.request.user)
        if booking.user.email:
            # Sent in the background by a Celery worker. If the broker is down,
            # keep the booking and log the problem instead of failing the request.
            try:
                send_booking_confirmation_email.delay(booking.id, booking.user.email)
            except Exception:  # noqa: BLE001 - any broker/connection error
                logger.exception('Could not queue the confirmation email for booking %s', booking.id)


class ReviewViewSet(viewsets.ModelViewSet):
    """Anyone can read reviews; signed-in users can post and edit their own."""
    queryset = Review.objects.select_related('user', 'listing')
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            raise PermissionDenied('You can only edit your own reviews.')
        serializer.save()


# ---------------- Chapa payments ----------------
import uuid

import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Payment
from .serializers import PaymentSerializer


def chapa_headers():
    return {'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}', 'Content-Type': 'application/json'}


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_payment(request):
    """Start a Chapa payment for one of your bookings. Body: {"booking": <id>}."""
    if not settings.CHAPA_SECRET_KEY:
        return Response({'error': 'CHAPA_SECRET_KEY is not configured.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    booking = get_object_or_404(Booking, pk=request.data.get('booking'), user=request.user)
    reference = f'booking-{booking.id}-{uuid.uuid4().hex[:10]}'
    payload = {
        'amount': str(booking.total_price),
        'currency': 'ETB',
        'email': request.user.email or 'guest@example.com',
        'first_name': request.user.first_name or request.user.username,
        'last_name': request.user.last_name or 'Guest',
        'tx_ref': reference,
        'return_url': f'{settings.CHAPA_RETURN_URL}?tx_ref={reference}',
        'customization': {'title': 'ALX Travel', 'description': f'Booking {booking.id}'},
    }
    try:
        response = requests.post(f'{settings.CHAPA_BASE_URL}/transaction/initialize', json=payload, headers=chapa_headers(), timeout=15)
        data = response.json()
    except (requests.RequestException, ValueError):
        return Response({'error': 'Could not reach Chapa.'}, status=status.HTTP_502_BAD_GATEWAY)

    if response.status_code != 200 or data.get('status') != 'success':
        return Response({'error': 'Chapa rejected the payment.', 'details': data}, status=status.HTTP_400_BAD_REQUEST)

    payment = Payment.objects.create(booking=booking, booking_reference=reference, amount=booking.total_price)
    return Response(
        {'payment': PaymentSerializer(payment).data, 'checkout_url': data['data']['checkout_url']},
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verify_payment(request):
    """Check a payment with Chapa and update its status. Query: ?tx_ref=<booking_reference>."""
    payment = get_object_or_404(Payment, booking_reference=request.query_params.get('tx_ref'))
    try:
        response = requests.get(f'{settings.CHAPA_BASE_URL}/transaction/verify/{payment.booking_reference}', headers=chapa_headers(), timeout=15)
        data = response.json()
    except (requests.RequestException, ValueError):
        return Response({'error': 'Could not reach Chapa.'}, status=status.HTTP_502_BAD_GATEWAY)

    if data.get('status') == 'success' and data.get('data', {}).get('status') == 'success':
        payment.status = Payment.Status.COMPLETED
        payment.transaction_id = data['data'].get('reference') or payment.transaction_id
        payment.booking.status = Booking.Status.CONFIRMED
        payment.booking.save(update_fields=['status'])
    else:
        payment.status = Payment.Status.FAILED
    payment.save()
    return Response(PaymentSerializer(payment).data)
