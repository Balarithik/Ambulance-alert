from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, SensorReadingViewSet

router = DefaultRouter()
router.register(r'readings', SensorReadingViewSet, basename='sensor-readings')
router.register(r'', PatientViewSet, basename='patients')

urlpatterns = [
    path('', include(router.urls)),
]
