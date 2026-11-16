from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BookingViewSet,
    InitiatePaymentView,
    ListingViewSet,
    PaymentViewSet,
    ReviewViewSet,
    VerifyPaymentView,
)

router = DefaultRouter()
router.register(r"listings", ListingViewSet, basename="listing")
router.register(r"bookings", BookingViewSet, basename="booking")
router.register(r"reviews", ReviewViewSet, basename="review")
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    # Listed before the router so they are not read as payment IDs.
    path("payments/initiate/", InitiatePaymentView.as_view(), name="initiate-payment"),
    path("payments/verify/<str:tx_ref>/", VerifyPaymentView.as_view(), name="verify-payment"),
    path("", include(router.urls)),
]
