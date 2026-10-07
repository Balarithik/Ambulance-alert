from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AmbulanceViewSet, DemoDataViewSet

router = DefaultRouter()
router.register(r'demo', DemoDataViewSet, basename='demo')
router.register(r'', AmbulanceViewSet, basename='ambulances')

urlpatterns = [
    path('', include(router.urls)),
]
