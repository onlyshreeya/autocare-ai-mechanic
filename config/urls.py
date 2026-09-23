"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from chat import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/chat/', include('chat.urls')),
    path('api/upload/', views.upload_media, name='upload_media'),
    path('api/diagnosis/', views.diagnosis_api, name='diagnosis_api'),
    path('api/booking/', views.booking_api, name='booking_api'),
    path('api/booking/<int:booking_id>/', views.get_booking_by_id, name='get_booking_by_id'),
    path('api/bookings/', views.get_bookings, name='get_bookings'),
    path('api/bookings/<int:booking_id>/status/', views.update_booking_status, name='update_booking_status'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )