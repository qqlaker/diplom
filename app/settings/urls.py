from core.views import HealthView
from django.contrib import admin
from django.urls import path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


admin.site.site_header = "Diplom"
admin.site.index_title = "Diplom"


urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    re_path(r"^api/swagger/$", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("admin/", admin.site.urls),
    path("api/health/", HealthView.as_view()),
]
