from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/patients/', include('patients.urls')),
    path('api/ml/', include('ml_engine.urls')),
    path('api/ambulance/', include('ambulance.urls')),
    path('api/hospital/', include('hospital.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
