from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from io import StringIO

from .models import Booking, Listing, Review


class ModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('guest', 'guest@example.com', 'Str0ng-pass!')
        self.listing = Listing.objects.create(title='Cabin', description='Quiet', location='Kigali', price_per_night=Decimal('80'))

    def test_booking_total_price(self):
        booking = Booking.objects.create(listing=self.listing, user=self.user, check_in=date(2026, 1, 1), check_out=date(2026, 1, 4))
        self.assertEqual(booking.nights, 3)
        self.assertEqual(booking.total_price, Decimal('240.00'))

    def test_review(self):
        review = Review.objects.create(listing=self.listing, user=self.user, rating=5)
        self.assertIn('Cabin', str(review))

    def test_seed_command(self):
        call_command('seed', '--listings', '3', stdout=StringIO())
        self.assertEqual(Listing.objects.count(), 4)
        self.assertEqual(Booking.objects.count(), 3)

    def test_swagger_docs(self):
        self.assertEqual(self.client.get('/swagger/?format=openapi').status_code, 200)


from rest_framework.test import APITestCase


class ApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.host = User.objects.create_user('host', 'host@example.com', 'Str0ng-pass!')
        self.guest = User.objects.create_user('guest', 'guest@example.com', 'Str0ng-pass!')
        self.listing = Listing.objects.create(host=self.host, title='Villa', description='Sea view', location='Mombasa', price_per_night=Decimal('100'))

    def book(self, nights=2):
        start = date.today() + timedelta(days=10)
        return self.client.post('/api/bookings/', {'listing': self.listing.id, 'check_in': start, 'check_out': start + timedelta(days=nights)}, format='json')

    def test_anyone_can_browse_listings(self):
        response = self.client.get('/api/listings/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['title'], 'Villa')

    def test_create_and_edit_listing(self):
        self.assertEqual(self.client.post('/api/listings/', {}, format='json').status_code, 403)
        self.client.force_authenticate(self.host)
        response = self.client.post('/api/listings/', {'title': 'Loft', 'description': 'City', 'location': 'Accra', 'price_per_night': '60.00'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['host'], 'host')
        self.client.force_authenticate(self.guest)
        self.assertEqual(self.client.patch(f"/api/listings/{response.data['id']}/", {'title': 'Mine'}, format='json').status_code, 403)

    def test_booking_flow(self):
        self.client.force_authenticate(self.guest)
        response = self.book(nights=3)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['total_price'], '300.00')
        self.assertEqual(len(self.client.get('/api/bookings/').data['results']), 1)
        # Other users can't see it
        self.client.force_authenticate(self.host)
        self.assertEqual(len(self.client.get('/api/bookings/').data['results']), 0)

    def test_booking_dates_validated(self):
        self.client.force_authenticate(self.guest)
        self.assertEqual(self.book(nights=0).status_code, 400)


from unittest import mock

from django.test import override_settings

from .models import Payment


def fake_response(status_code, payload):
    response = mock.Mock(status_code=status_code)
    response.json.return_value = payload
    return response


@override_settings(CHAPA_SECRET_KEY='CHASECK_TEST-123')
class PaymentTests(ApiTests):
    def make_booking(self):
        self.client.force_authenticate(self.guest)
        return self.book(nights=2).data['id']

    @mock.patch('listings.views.requests.post')
    def test_initiate_payment(self, post):
        post.return_value = fake_response(200, {'status': 'success', 'data': {'checkout_url': 'https://checkout.chapa.co/abc'}})
        response = self.client.post('/api/payments/initiate/', {'booking': self.make_booking()}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['checkout_url'], 'https://checkout.chapa.co/abc')
        self.assertEqual(Payment.objects.get().amount, Decimal('200.00'))
        self.assertEqual(post.call_args.kwargs['json']['amount'], '200.00')

    @mock.patch('listings.views.requests.get')
    @mock.patch('listings.views.requests.post')
    def test_verify_payment(self, post, get):
        post.return_value = fake_response(200, {'status': 'success', 'data': {'checkout_url': 'https://checkout.chapa.co/abc'}})
        booking_id = self.make_booking()
        reference = self.client.post('/api/payments/initiate/', {'booking': booking_id}, format='json').data['payment']['booking_reference']

        get.return_value = fake_response(200, {'status': 'success', 'data': {'status': 'success', 'reference': 'CHAPA-REF-1'}})
        response = self.client.get('/api/payments/verify/', {'tx_ref': reference})
        self.assertEqual(response.data['status'], 'Completed')
        self.assertEqual(Booking.objects.get(pk=booking_id).status, 'confirmed')

    @mock.patch('listings.views.requests.post')
    def test_chapa_rejects(self, post):
        post.return_value = fake_response(400, {'status': 'failed', 'message': 'Invalid key'})
        response = self.client.post('/api/payments/initiate/', {'booking': self.make_booking()}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Payment.objects.exists())

    def test_cannot_pay_for_someone_elses_booking(self):
        booking_id = self.make_booking()
        self.client.force_authenticate(self.host)
        self.assertEqual(self.client.post('/api/payments/initiate/', {'booking': booking_id}, format='json').status_code, 404)


from django.core import mail


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailTests(ApiTests):
    def test_booking_sends_confirmation_email(self):
        from alx_travel_app.celery import app
        app.conf.task_always_eager = True
        self.client.force_authenticate(self.guest)
        self.assertEqual(self.book(nights=2).status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Villa', mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ['guest@example.com'])
