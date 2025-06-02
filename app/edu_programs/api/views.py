# edu_programs/views.py
from django.db.models import (
    Avg,
    Case,
    Count,
    ExpressionWrapper,
    F,
    FloatField,
    Value,
    When,
)
from django.db.models.functions import ExtractYear
from django.shortcuts import render

from edu_programs.models import Competency, Faculty, Program, University


def analytics_dashboard(request):
    # Фильтрация
    faculty_id = request.GET.get("faculty")
    year = request.GET.get("year")

    # Базовый QuerySet
    base_programs = Program.objects.all()
    if faculty_id:
        base_programs = base_programs.filter(faculty_id=faculty_id)
    if year:
        base_programs = base_programs.filter(approval_year__year=year)

    # Основные аннотации для программ
    programs = (
        base_programs.select_related(
            "university",
            "faculty",
        )
        .prefetch_related(
            "disciplines",
            "professional_standards",
            "disciplines__competencies",
        )
        .annotate(
            calculated_demand_score=ExpressionWrapper(
                Case(
                    When(applicants_count=0, then=Value(0, output_field=FloatField())),
                    default=ExpressionWrapper(
                        0.6
                        * Case(
                            When(applicants_count=0, then=Value(0)),
                            default=F("graduates_employed") * 100.0 / F("applicants_count"),
                            output_field=FloatField(),
                        )
                        + 0.4 * (Count("disciplines") / 10.0),
                        output_field=FloatField(),
                    ),
                ),
                output_field=FloatField(),
            ),
            calculated_uniqueness_score=ExpressionWrapper(
                0.7 * Count("disciplines__competencies", distinct=True) + 0.3 * Count("disciplines", distinct=True),
                output_field=FloatField(),
            ),
            competencies_count=Count("disciplines__competencies", distinct=True),
        )
        .annotate(
            calculated_competitiveness=ExpressionWrapper(
                0.7 * F("calculated_demand_score") + 0.3 * F("calculated_uniqueness_score"),
                output_field=FloatField(),
            ),
        )
    )

    # Остальной код представления остается без изменений
    yearly_stats = (
        base_programs.values(
            year=ExtractYear("approval_year"),
        )
        .annotate(
            count=Count("id"),
            avg_credits=Avg("total_credits", output_field=FloatField()),
            avg_duration=Avg("duration_years", output_field=FloatField()),
        )
        .order_by("year")
    )

    university_stats = University.objects.annotate(
        program_count=Count("program"),
    ).order_by("-program_count")

    competency_stats = (
        Competency.objects.values(
            "type",
        )
        .annotate(
            count=Count("id"),
            program_count=Count("discipline__program", distinct=True),
        )
        .order_by("type")
    )

    context = {
        "faculties": Faculty.objects.all(),
        "years": Program.objects.dates("approval_year", "year"),
        "filters": {"faculty": faculty_id, "year": year},
        "top_demand": programs.order_by("-calculated_demand_score")[:5],
        "top_unique": programs.order_by("-calculated_uniqueness_score")[:5],
        "top_competitive": programs.order_by("-calculated_competitiveness")[:5],
        "yearly_stats": yearly_stats,
        "university_stats": university_stats,
        "competency_stats": competency_stats,
        "total_programs": base_programs.count(),
        "avg_demand": programs.aggregate(avg=Avg("calculated_demand_score", output_field=FloatField()))["avg"],
        "avg_competencies": programs.aggregate(avg=Avg("competencies_count", output_field=FloatField()))["avg"],
    }

    return render(request, "analytics/dashboard.html", context)


def get_yearly_stats(faculty_id=None):
    qs = Program.objects
    if faculty_id:
        qs = qs.filter(faculty_id=faculty_id)
    return (
        qs.annotate(
            year=ExtractYear("approval_year"),
        )
        .values("year")
        .annotate(
            avg_duration=Avg("duration_years"),
            avg_credits=Avg("total_credits"),
            avg_demand=Avg("demand_score"),
            count=Count("id"),
        )
        .order_by("year")
    )


def get_university_stats():
    return University.objects.annotate(
        program_count=Count("program"),
        avg_demand=Avg("program__demand_score"),
    ).order_by("-program_count")


def get_competency_stats():
    return (
        Competency.objects.annotate(
            program_count=Count("discipline__program", distinct=True),
        )
        .values("type", "program_count")
        .annotate(
            count=Count("id"),
        )
        .order_by("type")
    )
