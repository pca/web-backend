from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularJSONAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", include("api.urls")),
    path("admin/", admin.site.urls),
    path("openapi.json", SpectacularJSONAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]
