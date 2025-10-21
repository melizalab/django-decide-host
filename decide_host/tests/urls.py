from django.contrib import admin
from django.contrib.auth import views as authviews
from django.urls import include, path

urlpatterns = [
    path("decide/", include("decide_host.urls")),
    path("admin/", admin.site.urls),
    path("accounts/api-auth/", include("rest_framework.urls")),
]
