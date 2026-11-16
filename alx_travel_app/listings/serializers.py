from django.db.models import Avg, Count
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers

from .models import Booking, Listing, Payment, Review


class ListingSerializer(serializers.ModelSerializer):
    host = serializers.HiddenField(default=serializers.CurrentUserDefault())
    host_username = serializers.ReadOnlyField(source="host.username")
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            "id",
            "host",
            "host_username",
            "title",
            "description",
            "location",
            "price_per_night",
            "average_rating",
            "review_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    # The list/detail queryset annotates these; a freshly created or updated
    # instance has no annotation, so compute them on demand.
    def _review_stats(self, obj):
        if not hasattr(obj, "average_rating"):
            stats = obj.reviews.aggregate(average_rating=Avg("rating"), review_count=Count("id"))
            obj.average_rating = stats["average_rating"]
            obj.review_count = stats["review_count"]
        return obj

    @swagger_serializer_method(serializer_or_field=serializers.FloatField(allow_null=True))
    def get_average_rating(self, obj):
        value = self._review_stats(obj).average_rating
        return None if value is None else round(float(value), 2)

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField())
    def get_review_count(self, obj):
        return self._review_stats(obj).review_count


class BookingSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    guest_username = serializers.ReadOnlyField(source="user.username")
    nights = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "listing",
            "user",
            "guest_username",
            "check_in",
            "check_out",
            "nights",
            "total_price",
            "status",
            "created_at",
        ]
        read_only_fields = ["total_price", "status", "created_at"]

    def validate(self, attrs):
        instance = self.instance
        listing = attrs.get("listing", instance.listing if instance else None)
        check_in = attrs.get("check_in", instance.check_in if instance else None)
        check_out = attrs.get("check_out", instance.check_out if instance else None)

        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError({"check_out": "Check-out must be after check-in."})

        overlapping = Booking.objects.filter(
            listing=listing,
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).exclude(status=Booking.Status.CANCELLED)
        if instance is not None:
            overlapping = overlapping.exclude(pk=instance.pk)
        if overlapping.exists():
            raise serializers.ValidationError("This listing is already booked for those dates.")

        attrs["total_price"] = listing.price_per_night * (check_out - check_in).days
        return attrs


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Review
        fields = ["id", "listing", "user", "username", "rating", "comment", "created_at"]
        read_only_fields = ["created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "booking",
            "booking_reference",
            "transaction_id",
            "amount",
            "currency",
            "status",
            "checkout_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class InitiatePaymentSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
