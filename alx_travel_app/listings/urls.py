from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'listings', views.ListingViewSet, basename='listing')
router.register(r'bookings', views.BookingViewSet, basename='booking')
router.register(r'reviews', views.ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
    path('payments/initiate/', views.initiate_payment, name='payment-initiate'),
    path('payments/verify/', views.verify_payment, name='payment-verify'),
]
