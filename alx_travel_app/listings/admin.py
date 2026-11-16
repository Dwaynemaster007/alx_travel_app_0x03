from django.contrib import admin

from .models import Booking, Listing, Payment, Review


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "location", "price_per_night", "host", "created_at")
    search_fields = ("title", "location")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "listing", "user", "check_in", "check_out", "total_price", "status")
    list_filter = ("status",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("listing", "user", "rating", "created_at")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("booking_reference", "booking", "amount", "currency", "status", "created_at")
    list_filter = ("status",)
