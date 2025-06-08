from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from edu_programs.models import (
    EducationGroup,
    EduDegree,
    Faculty,
    FederalStateEducationStandard,
    ProfessionalStandard,
    ProfessionalStandardGroup,
    Program,
    University,
)


@admin.register(University)
class UniversityAdmin(SimpleHistoryAdmin):
    list_display = ("name", "abbreviation")
    search_fields = ("name", "abbreviation")
    list_filter = ("name",)


@admin.register(Faculty)
class FacultyAdmin(SimpleHistoryAdmin):
    list_display = ("name", "abbreviation", "university")
    search_fields = ("name", "abbreviation", "university__name")
    list_filter = ("university",)


@admin.register(ProfessionalStandardGroup)
class ProfessionalStandardGroupAdmin(SimpleHistoryAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(EducationGroup)
class EducationGroupAdmin(SimpleHistoryAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(ProfessionalStandard)
class ProfessionalStandardAdmin(SimpleHistoryAdmin):
    list_display = ("full_code", "name", "code", "professional_standard_group")
    search_fields = ("name", "code", "professional_standard_group__name")
    list_filter = ("professional_standard_group",)

    def full_code(self, obj):
        return f"{obj.professional_standard_group.code}.{obj.code}"

    full_code.short_description = "Полный код"
    full_code.admin_order_field = "code"


@admin.register(EduDegree)
class EduDegreeAdmin(SimpleHistoryAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(FederalStateEducationStandard)
class FederalStateEducationStandardAdmin(SimpleHistoryAdmin):
    list_display = ("full_code", "name", "code", "edu_group", "edu_degree")
    search_fields = ("name", "code", "edu_group__name", "edu_degree__name")
    list_filter = ("edu_group", "edu_degree")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "edu_group",
                    "edu_degree",
                    "code",
                ),
            },
        ),
    )

    def full_code(self, obj):
        return f"{obj.edu_group.code}.{obj.edu_degree.code}.{obj.code}"

    full_code.short_description = "Полный код"
    full_code.admin_order_field = "code"


@admin.register(Program)
class ProgramAdmin(SimpleHistoryAdmin):
    list_display = (
        "full_code",
        "code",
        "name",
        "profile",
        "university",
        "faculty",
        "edu_degree",
        "approval_year",
    )
    search_fields = ("code", "name", "university__name", "faculty__name", "edu_group__name")
    list_filter = (
        "university",
        "faculty",
        "edu_degree",
    )
    filter_horizontal = ("professional_standards",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "university",
                    "faculty",
                    "name",
                    "edu_group",
                    "edu_degree",
                    "code",
                    "profile",
                    "approval_year",
                    "professional_standards",
                    "document",
                ),
            },
        ),
    )

    def full_code(self, obj):
        return f"{obj.edu_group.code}.{obj.edu_degree.code}.{obj.code}"

    full_code.short_description = "Полный код"
    full_code.admin_order_field = "code"
