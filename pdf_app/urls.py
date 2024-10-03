from . import views
from pathlib import Path
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('', views.home),
    path('', views.pdf_manager, name='pdf_manager'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
