from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models.competencies import Competence, ProfessionalStandard
from .models.curriculum import Discipline
from .models.education import EducationalProgram
from .models.institutions import Faculty, University


class UniversityAdmin(SimpleHistoryAdmin):
    list_display = ("short_name", "name", "established")
    list_display_links = ("short_name", "name")
    search_fields = ("name", "short_name")
    list_filter = ("established",)
    ordering = ("name",)


class FacultyAdmin(SimpleHistoryAdmin):
    list_display = ("code", "name", "university")
    list_display_links = ("code", "name")
    search_fields = ("name", "code", "university__name")
    list_filter = ("university",)
    ordering = ("university__name", "name")


class EducationalProgramAdmin(SimpleHistoryAdmin):
    list_display = ("code", "name", "faculty", "degree", "is_active")
    list_display_links = ("code", "name")
    search_fields = ("name", "code", "faculty__name")
    list_filter = ("faculty__university", "faculty", "degree", "is_active")
    ordering = ("faculty__university__name", "faculty__name", "code")
    date_hierarchy = "approval_date"
    filter_horizontal = ()


class DisciplineAdmin(SimpleHistoryAdmin):
    list_display = ("code", "name", "program", "semester", "credits")
    list_display_links = ("code", "name")
    search_fields = ("name", "code", "program__name")
    list_filter = ("program__faculty", "semester")
    ordering = ("program__faculty__name", "semester", "code")
    filter_horizontal = ("competences",)


class CompetenceAdmin(SimpleHistoryAdmin):
    list_display = ("code", "type", "program", "short_name")
    list_display_links = ("code", "short_name")
    search_fields = ("name", "code", "program__name")
    list_filter = ("program__faculty", "type")
    ordering = ("program__faculty__name", "code")

    def short_name(self, obj):
        return obj.name[:100] + "..." if len(obj.name) > 100 else obj.name  # noqa: PLR2004

    short_name.short_description = "Формулировка"


class ProfessionalStandardAdmin(SimpleHistoryAdmin):
    list_display = ("code", "short_name", "registration_number", "approval_date")
    list_display_links = ("code", "short_name")
    search_fields = ("name", "code", "registration_number")
    list_filter = ("approval_date",)
    ordering = ("code",)
    date_hierarchy = "approval_date"

    def short_name(self, obj):
        return obj.name[:100] + "..." if len(obj.name) > 100 else obj.name  # noqa: PLR2004

    short_name.short_description = "Название"


admin.site.register(University, UniversityAdmin)
admin.site.register(Faculty, FacultyAdmin)
admin.site.register(EducationalProgram, EducationalProgramAdmin)
admin.site.register(Discipline, DisciplineAdmin)
admin.site.register(Competence, CompetenceAdmin)
admin.site.register(ProfessionalStandard, ProfessionalStandardAdmin)
