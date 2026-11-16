import logging
import uuid

from django.conf import settings
from django.db import transaction
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django.urls import reverse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from . import chapa
from .models import Booking, Listing, Payment, Review
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    BookingSerializer,
    InitiatePaymentSerializer,
    ListingSerializer,
    PaymentSerializer,
    ReviewSerializer,
)
from .tasks import send_booking_confirmation_email

logger = logging.getLogger(__name__)


class ListingViewSet(viewsets.ModelViewSet):
    """CRUD for listings. Anyone can read; only the host can edit or delete."""

    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    owner_field = "host"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "location"]
    ordering_fields = ["price_per_night", "created_at"]

    def get_queryset(self):
        return (
            Listing.objects.select_related("host")
            .annotate(average_rating=Avg("reviews__rating"), review_count=Count("reviews"))
            .order_by("-created_at")
        )


class BookingViewSet(viewsets.ModelViewSet):
    """CRUD for the signed-in user's bookings (staff see all bookings).

    Creating a booking queues a confirmation email through Celery.
    """

    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        queryset = Booking.objects.select_related("listing", "user")
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(user=user)

    def perform_create(self, serializer):
        booking = serializer.save()
        transaction.on_commit(lambda: queue_confirmation_email(booking))


def queue_confirmation_email(booking):
    """Hand the confirmation email to Celery without failing the request."""
    try:
        send_booking_confirmation_email.delay(booking.id, booking.user.email)
    except Exception:  # broker down, SMTP error in eager mode, ...
        logger.exception("Could not queue confirmation email for booking %s", booking.id)


class ReviewViewSet(viewsets.ModelViewSet):
    """CRUD for reviews. Anyone can read; only the author can edit or delete."""

    queryset = Review.objects.select_related("listing", "user")
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """The signed-in user's payments (staff see all payments)."""

    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Payment.objects.none()
        queryset = Payment.objects.select_related("booking")
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(booking__user=user)


class InitiatePaymentView(APIView):
    """Start a Chapa payment for one of your bookings and get its checkout URL."""

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=InitiatePaymentSerializer, responses={201: PaymentSerializer})
    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bookings = Booking.objects.select_related("user")
        if not request.user.is_staff:
            bookings = bookings.filter(user=request.user)
        booking = get_object_or_404(bookings, pk=serializer.validated_data["booking_id"])

        if booking.status == Booking.Status.CANCELLED:
            return Response({"detail": "This booking is cancelled."}, status=status.HTTP_400_BAD_REQUEST)
        if booking.payments.filter(status=Payment.Status.COMPLETED).exists():
            return Response({"detail": "This booking is already paid."}, status=status.HTTP_400_BAD_REQUEST)
        if not settings.CHAPA_SECRET_KEY:
            return Response(
                {"detail": "Payments are not configured (CHAPA_SECRET_KEY is not set)."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        tx_ref = f"booking-{booking.id}-{uuid.uuid4().hex[:12]}"
        callback_url = settings.CHAPA_CALLBACK_URL or request.build_absolute_uri(
            reverse("verify-payment", args=[tx_ref])
        )
        payload = {
            "amount": str(booking.total_price),
            "currency": settings.CHAPA_CURRENCY,
            "tx_ref": tx_ref,
            "callback_url": callback_url,
            "first_name": booking.user.first_name,
            "last_name": booking.user.last_name,
            "customization": {"title": "ALX Travel", "description": f"Booking {booking.id}"},
        }
        if booking.user.email:
            payload["email"] = booking.user.email
        if settings.CHAPA_RETURN_URL:
            payload["return_url"] = settings.CHAPA_RETURN_URL

        payment = Payment(
            booking=booking,
            booking_reference=tx_ref,
            amount=booking.total_price,
            currency=settings.CHAPA_CURRENCY,
        )
        try:
            data = chapa.initialize_transaction(payload)
        except chapa.ChapaError as exc:
            payment.status = Payment.Status.FAILED
            payment.save()
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        payment.checkout_url = data["data"]["checkout_url"]
        payment.save()
        body = PaymentSerializer(payment).data
        return Response(body, status=status.HTTP_201_CREATED)


class VerifyPaymentView(APIView):
    """Ask Chapa for a transaction's status and update the payment.

    Also used as Chapa's callback URL, so it needs no authentication: it only
    trusts what Chapa itself reports for the given tx_ref.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @swagger_auto_schema(responses={200: PaymentSerializer})
    def get(self, request, tx_ref):
        payment = get_object_or_404(Payment.objects.select_related("booking"), booking_reference=tx_ref)

        try:
            data = chapa.verify_transaction(tx_ref)
        except chapa.ChapaNotConfigured as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except chapa.ChapaError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        chapa_status = (data.get("data") or {}).get("status")
        with transaction.atomic():
            if chapa_status == "success":
                payment.status = Payment.Status.COMPLETED
                payment.transaction_id = data["data"].get("reference") or payment.transaction_id
                booking = payment.booking
                if booking.status == Booking.Status.PENDING:
                    booking.status = Booking.Status.CONFIRMED
                    booking.save(update_fields=["status"])
            elif chapa_status in ("failed", "cancelled"):
                payment.status = Payment.Status.FAILED
            payment.save()

        return Response(PaymentSerializer(payment).data)
