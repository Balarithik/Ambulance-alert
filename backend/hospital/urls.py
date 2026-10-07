from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HospitalPreparationViewSet

router = DefaultRouter()
router.register(r'preparations', HospitalPreparationViewSet, basename='hospital-preparations')

urlpatterns = [
    path('', include(router.urls)),
]
