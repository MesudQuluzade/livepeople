from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [path('django-admin/', admin.site.urls), path('', include('core.urls'))]

# Vercel routes requests through the Django function. Serve the existing
# frontend assets there as well so the original UI is preserved in production.
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
