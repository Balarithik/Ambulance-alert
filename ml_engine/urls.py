from django.urls import path
from . import views

urlpatterns = [
    path("predict/", views.MLEngineViewSet.as_view({"post": "predict"})),
    path("health/", views.MLEngineViewSet.as_view({"get": "health"})),
    path("reset/", views.MLEngineViewSet.as_view({"post": "reset"})),
    path("record-risk/", views.MLEngineViewSet.as_view({"post": "record_risk"})),
]
