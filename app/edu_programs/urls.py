# edu_programs/urls.py
from django.urls import path

from .api import views


urlpatterns = [
    path("", views.analytics_dashboard, name="home"),
    path("analytics/", views.analytics_dashboard, name="analytics"),
]
