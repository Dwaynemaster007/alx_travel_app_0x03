import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from listings.models import Booking, Listing, Review

TITLES = [
    "Beachside Bungalow",
    "Mountain Retreat",
    "Downtown Apartment",
    "Cozy Cabin",
    "Luxury Villa",
    "Lakeside Cottage",
    "Safari Lodge",
    "Garden Studio",
]
LOCATIONS = ["Mombasa", "Nairobi", "Kigali", "Cape Town", "Accra", "Addis Ababa", "Lagos", "Zanzibar"]
COMMENTS = [
    "Wonderful stay, would book again.",
    "Clean, comfortable and close to everything.",
    "Great host and a beautiful view.",
    "Good value for the price.",
    "",
]


class Command(BaseCommand):
    help = "Seed the database with sample users, listings, bookings and reviews."

    def add_arguments(self, parser):
        parser.add_argument("--listings", type=int, default=10, help="Number of listings to create (default 10).")
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing listings (and their bookings, reviews and payments) first.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = Listing.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing objects."))

        host = self._user("seed_host", "host@example.com")
        guests = [self._user(f"seed_guest{i}", f"guest{i}@example.com") for i in (1, 2, 3)]

        today = timezone.localdate()
        bookings = reviews = 0
        for _ in range(options["listings"]):
            listing = Listing.objects.create(
                host=host,
                title=random.choice(TITLES),
                description="A wonderful place to stay!",
                location=random.choice(LOCATIONS),
                price_per_night=Decimal(random.randint(5000, 30000)) / 100,
            )
            # Non-overlapping stays, one after another.
            check_in = today + timedelta(days=random.randint(1, 14))
            for guest in random.sample(guests, k=random.randint(0, len(guests))):
                nights = random.randint(1, 7)
                check_out = check_in + timedelta(days=nights)
                Booking.objects.create(
                    listing=listing,
                    user=guest,
                    check_in=check_in,
                    check_out=check_out,
                    total_price=listing.price_per_night * nights,
                )
                bookings += 1
                check_in = check_out + timedelta(days=random.randint(0, 3))
            for guest in random.sample(guests, k=random.randint(0, len(guests))):
                Review.objects.create(
                    listing=listing,
                    user=guest,
                    rating=random.randint(3, 5),
                    comment=random.choice(COMMENTS),
                )
                reviews += 1
            self.stdout.write(f"Created listing: {listing} ({listing.location})")

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {options['listings']} listings, {bookings} bookings and {reviews} reviews."
            )
        )

    def _user(self, username, email):
        User = get_user_model()
        user, created = User.objects.get_or_create(username=username, defaults={"email": email})
        if created:
            user.set_password("password123")
            user.save()
            self.stdout.write(f"Created user {username} (password: password123)")
        return user
