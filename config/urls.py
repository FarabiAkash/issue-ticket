from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from accounts.views import HomeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("users/", include("accounts.user_urls")),
    path("companies/", include("organizations.company_urls")),
    path("projects/", include("organizations.project_urls")),
    path("tickets/", include("tickets.urls")),
    path("", HomeView.as_view(), name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
