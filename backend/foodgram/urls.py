from django.urls import path, include
from django.contrib import admin
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
    path(
        'docs/',
        TemplateView.as_view(template_name='redoc.html'),
        name='redoc'
    ),
]
