from datetime import date
from decimal import Decimal
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from . import chapa
from .models import Booking, Listing, Payment, Review

User = get_user_model()

TEST_SETTINGS = {
    "CELERY_TASK_ALWAYS_EAGER": True,
    "EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    "CHAPA_SECRET_KEY": "CHASECK_TEST-dummy",
}


def apply_celery_settings():
    # Celery reads its config once; mirror the overridden setting onto the app.
    from alx_travel_app.celery import app

    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True


@override_settings(**TEST_SETTINGS)
class BaseAPITest(APITestCase):
    def setUp(self):
        apply_celery_settings()
        self.host = User.objects.create_user("host", "host@example.com", "pass12345")
        self.guest = User.objects.create_user("guest", "guest@example.com", "pass12345")
        self.listing = Listing.objects.create(
            host=self.host,
            title="Cozy Cabin",
            description="Quiet and warm.",
            location="Nairobi",
            price_per_night=Decimal("100.00"),
        )

    def make_booking(self, user=None, check_in=date(2030, 1, 1), check_out=date(2030, 1, 4)):
        return Booking.objects.create(
            listing=self.listing,
            user=user or self.guest,
            check_in=check_in,
            check_out=check_out,
            total_price=self.listing.price_per_night * (check_out - check_in).days,
        )


class ListingAPITests(BaseAPITest):
    def test_anyone_can_list_listings(self):
        response = self.client.get("/api/listings/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["host_username"], "host")

    def test_anonymous_cannot_create_listing(self):
        response = self.client.post("/api/listings/", {"title": "x"})
        self.assertIn(response.status_code, (401, 403))

    def test_create_update_delete_listing(self):
        self.client.force_authenticate(self.host)
        response = self.client.post(
            "/api/listings/",
            {"title": "Villa", "description": "Big", "location": "Accra", "price_per_night": "250.00"},
        )
        self.assertEqual(response.status_code, 201, response.data)
        listing_id = response.data["id"]
        self.assertEqual(response.data["review_count"], 0)
        self.assertIsNone(response.data["average_rating"])
        self.assertEqual(Listing.objects.get(pk=listing_id).host, self.host)

        response = self.client.patch(f"/api/listings/{listing_id}/", {"price_per_night": "199.99"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["price_per_night"], "199.99")

        response = self.client.delete(f"/api/listings/{listing_id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Listing.objects.filter(pk=listing_id).exists())

    def test_only_host_can_edit_listing(self):
        self.client.force_authenticate(self.guest)
        response = self.client.patch(f"/api/listings/{self.listing.id}/", {"title": "Mine now"})
        self.assertEqual(response.status_code, 403)

    def test_search_by_location(self):
        response = self.client.get("/api/listings/", {"search": "nairobi"})
        self.assertEqual(response.data["count"], 1)
        response = self.client.get("/api/listings/", {"search": "lagos"})
        self.assertEqual(response.data["count"], 0)


class BookingAPITests(BaseAPITest):
    def test_bookings_require_login(self):
        self.assertIn(self.client.get("/api/bookings/").status_code, (401, 403))

    def test_create_booking_computes_price_and_sends_email(self):
        self.client.force_authenticate(self.guest)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                "/api/bookings/",
                {"listing": self.listing.id, "check_in": "2030-02-01", "check_out": "2030-02-04"},
            )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["total_price"], "300.00")
        self.assertEqual(response.data["nights"], 3)
        self.assertEqual(response.data["status"], "pending")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["guest@example.com"])
        self.assertIn(f"#{response.data['id']}", mail.outbox[0].subject)

    def test_booking_still_created_when_task_cannot_be_queued(self):
        self.client.force_authenticate(self.guest)
        # assertLogs must wrap captureOnCommitCallbacks: the callbacks run when it exits.
        with self.assertLogs("listings.views", "ERROR"), mock.patch(
            "listings.views.send_booking_confirmation_email.delay",
            side_effect=ConnectionError("broker down"),
        ), self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                "/api/bookings/",
                {"listing": self.listing.id, "check_in": "2030-02-01", "check_out": "2030-02-02"},
            )
        self.assertEqual(response.status_code, 201)

    def test_check_out_must_be_after_check_in(self):
        self.client.force_authenticate(self.guest)
        response = self.client.post(
            "/api/bookings/",
            {"listing": self.listing.id, "check_in": "2030-02-04", "check_out": "2030-02-04"},
        )
        self.assertEqual(response.status_code, 400)

    def test_overlapping_booking_rejected(self):
        self.make_booking(check_in=date(2030, 3, 1), check_out=date(2030, 3, 5))
        self.client.force_authenticate(self.host)
        response = self.client.post(
            "/api/bookings/",
            {"listing": self.listing.id, "check_in": "2030-03-04", "check_out": "2030-03-06"},
        )
        self.assertEqual(response.status_code, 400)

    def test_users_only_see_their_own_bookings(self):
        self.make_booking()
        self.make_booking(user=self.host, check_in=date(2030, 5, 1), check_out=date(2030, 5, 2))
        self.client.force_authenticate(self.guest)
        response = self.client.get("/api/bookings/")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["guest_username"], "guest")

    def test_update_and_delete_booking(self):
        booking = self.make_booking()
        self.client.force_authenticate(self.guest)
        response = self.client.patch(f"/api/bookings/{booking.id}/", {"check_out": "2030-01-06"})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["total_price"], "500.00")
        self.assertEqual(self.client.delete(f"/api/bookings/{booking.id}/").status_code, 204)


class ReviewAPITests(BaseAPITest):
    def test_create_review_and_rating_shows_on_listing(self):
        self.client.force_authenticate(self.guest)
        response = self.client.post("/api/reviews/", {"listing": self.listing.id, "rating": 4, "comment": "Nice"})
        self.assertEqual(response.status_code, 201, response.data)
        listing = self.client.get(f"/api/listings/{self.listing.id}/").data
        self.assertEqual(listing["average_rating"], 4.0)
        self.assertEqual(listing["review_count"], 1)

    def test_one_review_per_user_per_listing(self):
        Review.objects.create(listing=self.listing, user=self.guest, rating=5)
        self.client.force_authenticate(self.guest)
        response = self.client.post("/api/reviews/", {"listing": self.listing.id, "rating": 3})
        self.assertEqual(response.status_code, 400)

    def test_rating_must_be_1_to_5(self):
        self.client.force_authenticate(self.guest)
        response = self.client.post("/api/reviews/", {"listing": self.listing.id, "rating": 6})
        self.assertEqual(response.status_code, 400)


class PaymentAPITests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.booking = self.make_booking()

    @mock.patch("listings.chapa.initialize_transaction")
    def test_initiate_payment(self, initialize):
        initialize.return_value = {
            "status": "success",
            "data": {"checkout_url": "https://checkout.chapa.co/checkout/payment/abc"},
        }
        self.client.force_authenticate(self.guest)
        response = self.client.post("/api/payments/initiate/", {"booking_id": self.booking.id})

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["checkout_url"], "https://checkout.chapa.co/checkout/payment/abc")
        self.assertEqual(response.data["status"], "Pending")
        self.assertEqual(response.data["amount"], "300.00")
        payload = initialize.call_args.args[0]
        self.assertEqual(payload["amount"], "300.00")
        self.assertEqual(payload["email"], "guest@example.com")
        self.assertIn(f"/api/payments/verify/{payload['tx_ref']}/", payload["callback_url"])

    @mock.patch("listings.chapa.initialize_transaction", side_effect=chapa.ChapaError("Invalid API key"))
    def test_initiate_payment_failure_is_recorded(self, _):
        self.client.force_authenticate(self.guest)
        response = self.client.post("/api/payments/initiate/", {"booking_id": self.booking.id})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(Payment.objects.get().status, Payment.Status.FAILED)

    def test_cannot_pay_for_someone_elses_booking(self):
        self.client.force_authenticate(self.host)
        response = self.client.post("/api/payments/initiate/", {"booking_id": self.booking.id})
        self.assertEqual(response.status_code, 404)

    @override_settings(CHAPA_SECRET_KEY="")
    def test_initiate_without_secret_key(self):
        self.client.force_authenticate(self.guest)
        response = self.client.post("/api/payments/initiate/", {"booking_id": self.booking.id})
        self.assertEqual(response.status_code, 503)

    @mock.patch("listings.chapa.verify_transaction")
    def test_verify_payment_completes_and_confirms_booking(self, verify):
        payment = Payment.objects.create(booking=self.booking, booking_reference="booking-1-abc", amount="300.00")
        verify.return_value = {"status": "success", "data": {"status": "success", "reference": "APabc123"}}

        response = self.client.get(f"/api/payments/verify/{payment.booking_reference}/")

        self.assertEqual(response.status_code, 200, response.data)
        payment.refresh_from_db()
        self.booking.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.COMPLETED)
        self.assertEqual(payment.transaction_id, "APabc123")
        self.assertEqual(self.booking.status, Booking.Status.CONFIRMED)

    def test_verify_unknown_reference(self):
        self.assertEqual(self.client.get("/api/payments/verify/nope/").status_code, 404)

    @mock.patch("listings.chapa.requests.post")
    def test_chapa_client_sends_secret_key(self, post):
        post.return_value = mock.Mock(status_code=200, json=lambda: {"status": "success", "data": {}})
        chapa.initialize_transaction({"amount": "1"})
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer CHASECK_TEST-dummy")


@override_settings(**TEST_SETTINGS)
class SeedAndDocsTests(TestCase):
    def test_seed_command(self):
        call_command("seed", "--listings", "5", stdout=StringIO())
        self.assertEqual(Listing.objects.count(), 5)
        self.assertTrue(User.objects.filter(username="seed_host").exists())

    def test_swagger_page(self):
        self.assertEqual(self.client.get("/swagger/").status_code, 200)
        response = self.client.get("/swagger.json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("/payments/initiate/", response.json()["paths"])
