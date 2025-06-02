import json

from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from edu_programs.const import POSSIBLE_QUALIFICATIONS
from edu_programs.models import Faculty, ProfessionalStandard, Program


def programs_dashboard(request):
    faculty_ids = [fid for fid in request.GET.getlist("faculties") if fid]
    qualification = request.GET.get("qualification", "")

    faculties = Faculty.objects.all()

    programs = Program.objects.select_related("faculty", "university").prefetch_related("professional_standards")
    if faculty_ids:
        faculty_ids = [int(fid) for fid in faculty_ids]
        program_codes = None
        for fid in faculty_ids:
            codes = set(Program.objects.filter(faculty__id=fid).values_list("code", flat=True))
            program_codes = codes if program_codes is None else program_codes.intersection(codes)
        programs = programs.filter(code__in=program_codes) if program_codes else programs.none()
    if qualification:
        programs = programs.filter(qualification__iexact=qualification)

    chart_labels = []
    chart_values = []
    qualification_counts = (
        programs.values("qualification").annotate(program_count=Count("id")).order_by("qualification")
    )

    counts_dict = dict.fromkeys(POSSIBLE_QUALIFICATIONS, 0)
    for item in qualification_counts:
        qual = item["qualification"].lower() if item["qualification"] else "другое"
        if qual not in counts_dict:
            qual = "другое"
        counts_dict[qual] += item["program_count"]

    for qual in POSSIBLE_QUALIFICATIONS:
        if counts_dict[qual] > 0:
            chart_labels.append(qual.capitalize())
            chart_values.append(counts_dict[qual])

    chart_data = {
        "labels": chart_labels,
        "values": chart_values,
    }

    context = {
        "faculties": faculties,
        "selected_faculties": faculty_ids,
        "qualification": qualification,
        "programs": programs,
        "chart_data": json.dumps(chart_data),
    }
    return render(request, "dashboards/programs_dashboard.html", context)


def programs_detail(request):
    program_code = request.GET.get("program_code", "")

    program_codes = Program.objects.values("code", "name").distinct()

    programs = Program.objects.select_related("faculty", "university").prefetch_related(
        "professional_standards", "disciplines", "disciplines__competencies"
    )
    if program_code:
        programs = programs.filter(code=program_code)

    for program in programs:
        program.competencies = (
            program.disciplines.prefetch_related("competencies")
            .values(
                "competencies__code",
                "competencies__description",
                "competencies__type",
            )
            .distinct()
        )

    chart_data = {
        "labels": [],
        "values": [],
    }
    profile_counts = Program.objects.values("code", "name").annotate(profile_count=Count("id")).order_by("code")
    if program_code:
        profile_counts = profile_counts.filter(code=program_code)
    for item in profile_counts:
        if item["code"]:
            chart_data["labels"].append(f"{item['code']} - {item['name']}")
            chart_data["values"].append(item["profile_count"])

    context = {
        "program_codes": program_codes,
        "program_code": program_code,
        "programs": programs,
        "chart_data": json.dumps(chart_data),
    }
    return render(request, "dashboards/programs_detail.html", context)


def download_programs_report(request):
    faculty_ids = [fid for fid in request.GET.getlist("faculties") if fid]
    qualification = request.GET.get("qualification", "")

    programs = Program.objects.select_related("faculty", "university").prefetch_related("professional_standards")
    if faculty_ids:
        faculty_ids = [int(fid) for fid in faculty_ids]
        program_codes = None
        for fid in faculty_ids:
            codes = set(Program.objects.filter(faculty__id=fid).values_list("code", flat=True))
            program_codes = codes if program_codes is None else program_codes.intersection(codes)
        programs = programs.filter(code__in=program_codes) if program_codes else programs.none()
    if qualification:
        programs = programs.filter(qualification__iexact=qualification)

    qualification_counts = (
        programs.values("qualification").annotate(program_count=Count("id")).order_by("qualification")
    )
    counts_dict = dict.fromkeys(POSSIBLE_QUALIFICATIONS, 0)
    for item in qualification_counts:
        qual = item["qualification"].lower() if item["qualification"] else "другое"
        if qual not in counts_dict:
            qual = "другое"
        counts_dict[qual] += item["program_count"]

    qualification_data = [
        {"qualification": qual.capitalize(), "count": counts_dict[qual]}
        for qual in POSSIBLE_QUALIFICATIONS
        if counts_dict[qual] > 0
    ]

    context = {
        "programs": programs,
        "qualification": qualification,
        "faculties": Faculty.objects.filter(id__in=faculty_ids) if faculty_ids else Faculty.objects.all(),
        "qualification_data": qualification_data,
    }

    response = render(request, "dashboards/programs_report.html", context)
    response["Content-Disposition"] = 'attachment; filename="programs_report.html"'
    return response


def program_detail_report(request, program_id):
    program = get_object_or_404(
        Program.objects.select_related("faculty", "university").prefetch_related(
            "professional_standards",
            "disciplines",
            "disciplines__competencies",
        ),
        id=program_id,
    )

    competencies = (
        program.disciplines.prefetch_related("competencies")
        .values(
            "competencies__code",
            "competencies__description",
            "competencies__type",
        )
        .distinct()
    )

    context = {
        "program": program,
        "standards": program.professional_standards.all(),
        "disciplines": program.disciplines.all(),
        "competencies": competencies,
    }

    response = render(request, "dashboards/programs_detail_report.html", context)
    response["Content-Disposition"] = f'attachment; filename="program_{program_id}_report.html"'
    return response


def standards_dashboard(request):
    faculty_ids = [fid for fid in request.GET.getlist("faculties") if fid]
    qualification = request.GET.get("qualification", "")

    faculties = Faculty.objects.all()

    programs = Program.objects.select_related("faculty", "university").prefetch_related("professional_standards")
    if faculty_ids:
        faculty_ids = [int(fid) for fid in faculty_ids]
        programs = programs.filter(faculty__id__in=faculty_ids)
    if qualification:
        programs = programs.filter(qualification__iexact=qualification)

    standards_by_year = (
        programs.values("approval_year")
        .annotate(standard_count=Count("professional_standards", distinct=True))
        .order_by("approval_year")
    )
    years = [item["approval_year"] for item in standards_by_year if item["approval_year"]]
    standard_counts = [item["standard_count"] for item in standards_by_year if item["approval_year"]]
    line_chart_data = {
        "labels": years,
        "values": standard_counts,
    }

    bar_chart_data = {
        "labels": [],
        "values": [],
    }
    standard_counts_by_qual = (
        programs.values("qualification")
        .annotate(standard_count=Count("professional_standards", distinct=True))
        .order_by("qualification")
    )
    counts_dict = dict.fromkeys(POSSIBLE_QUALIFICATIONS, 0)
    for item in standard_counts_by_qual:
        qual = item["qualification"].lower() if item["qualification"] else "другое"
        if qual not in counts_dict:
            qual = "другое"
        counts_dict[qual] = item["standard_count"]

    for qual in POSSIBLE_QUALIFICATIONS:
        if counts_dict[qual] > 0:
            bar_chart_data["labels"].append(qual.capitalize())
            bar_chart_data["values"].append(counts_dict[qual])

    standards = ProfessionalStandard.objects.prefetch_related("program_set__faculty").distinct()
    if faculty_ids or qualification:
        filtered_programs = programs.values_list("id", flat=True)
        standards = standards.filter(program__id__in=filtered_programs).distinct()

    context = {
        "faculties": faculties,
        "selected_faculties": faculty_ids,
        "qualification": qualification,
        "standards": standards,
        "line_chart_data": json.dumps(line_chart_data),
        "bar_chart_data": json.dumps(bar_chart_data),
    }
    return render(request, "dashboards/standards_dashboard.html", context)
