from django.urls import path

from .views import (
    download_programs_report,
    program_detail_report,
    programs_dashboard,
    programs_detail,
    standards_dashboard,
)


urlpatterns = [
    path("programs/", programs_dashboard, name="programs_dashboard"),
    path("programs/report/", download_programs_report, name="download_programs_report"),
    path("programs/detail/", programs_detail, name="programs_detail"),
    path("programs/detail/report/<int:program_id>/", program_detail_report, name="program_detail_report"),
    path("standards/", standards_dashboard, name="standards_dashboard"),
]
