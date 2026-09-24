from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', RedirectView.as_view(pattern_name='login', permanent=False)),
    path('', include('grievances.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
