from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from edu_programs.models import Competency, Discipline, Faculty, ProfessionalStandard, Program, University


@admin.register(University)
class UniversityAdmin(SimpleHistoryAdmin):
    list_display = ("name", "abbreviation", "location", "website")
    search_fields = ("name", "abbreviation", "location")
    list_filter = ("location",)


@admin.register(Faculty)
class FacultyAdmin(SimpleHistoryAdmin):
    list_display = ("name", "abbreviation", "university")
    search_fields = ("name", "abbreviation", "university__name")
    list_filter = ("university",)


@admin.register(ProfessionalStandard)
class ProfessionalStandardAdmin(SimpleHistoryAdmin):
    list_display = ("code", "title", "domain", "order_number", "order_date")
    search_fields = ("code", "title", "domain")
    list_filter = ("domain", "order_date")
    date_hierarchy = "order_date"


@admin.register(Competency)
class CompetencyAdmin(SimpleHistoryAdmin):
    list_display = ("code", "type", "short_description")
    search_fields = ("code", "description")
    list_filter = ("type",)

    def short_description(self, obj):
        return obj.description[:70] + "..." if len(obj.description) > 70 else obj.description

    short_description.short_description = "Описание"


@admin.register(Discipline)
class DisciplineAdmin(SimpleHistoryAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")
    filter_horizontal = ("competencies",)


@admin.register(Program)
class ProgramAdmin(SimpleHistoryAdmin):
    list_display = (
        "code",
        "name",
        "university",
        "faculty",
        "qualification",
        "duration_years",
        "approval_year",
        "is_processed",
    )
    search_fields = ("code", "name", "university__name")
    readonly_fields = ("is_processed", "processing_error")
    actions = ["reprocess_documents"]
    list_filter = (
        "university",
        "qualification",
        "language",
    )
    filter_horizontal = (
        "professional_standards",
        "disciplines",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "university",
                    "faculty",
                    "document",
                    "is_processed",
                    "code",
                    "name",
                    "profile",
                    "approval_year",
                ),
            },
        ),
        (
            "Квалификация",
            {
                "fields": ("qualification", "duration_years", "total_credits"),
            },
        ),
        (
            "Варианты обучения",
            {
                "fields": (
                    "language",
                    "contact_hours_min",
                ),
            },
        ),
        (
            "Профессиональные стандарты и дисциплины",
            {
                "fields": ("professional_standards", "disciplines"),
            },
        ),
    )

    def reprocess_documents(self, request, queryset):
        for program in queryset:
            if program.document:
                program.is_processed = False
                program.save()
        self.message_user(request, "Выбранные программы будут обработаны повторно")

    reprocess_documents.short_description = "Переобработать документы"
