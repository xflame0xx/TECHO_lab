from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .Models import ApplicantProfile, Application, ApplicationVacancy, Vacancy
from .services import (
    apply_status_change,
    ensure_draft_application,
    get_application_list_queryset,
    get_constant_creator,
    get_or_create_profile,
    parse_date,
    recalc_application_sum,
)


def home_redirect(request):
    return redirect("vacancies")


def build_application_context(app: Application, profile: ApplicantProfile) -> dict:
    lines = app.lines.select_related("vacancy").order_by("order_index", "id")
    total_positions = lines.count()
    total_sum = recalc_application_sum(app)
    return {
        "app": app,
        "profile": profile,
        "lines": lines,
        "total_positions": total_positions,
        "total_sum": total_sum,
        "status_choices": Application.Status.choices,
        "gender_choices": ApplicantProfile.Gender.choices,
        "category_choices": ApplicantProfile.DisabilityCategory.choices,
        "totalPositions": total_positions,
        "totalSum": total_sum,
        "statusChoices": Application.Status.choices,
        "genderChoices": ApplicantProfile.Gender.choices,
        "categoryChoices": ApplicantProfile.DisabilityCategory.choices,
    }


def vacancies_list(request):
    demo_user = get_constant_creator()
    search = request.GET.get("search", "").strip()

    qs = Vacancy.objects.filter(is_active=True)
    if search:
        qs = qs.filter(
            Q(title__icontains=search) | Q(company__icontains=search) | Q(city__icontains=search)
        )

    draft = Application.objects.filter(creator=demo_user, status=Application.Status.DRAFT).first()
    draft_count = draft.lines.count() if draft else 0

    return render(
        request,
        "vacancies.html",
        {
            "vacancies": qs.order_by("id"),
            "search": search,
            "draft": draft,
            "draft_count": draft_count,
            "draftCount": draft_count,
        },
    )


def vacancy_detail(request, id):
    vacancy = get_object_or_404(Vacancy, pk=id, is_active=True)
    return render(request, "vacancy.html", {"vacancy": vacancy})


def applications_list(request):
    demo_user = get_constant_creator()
    status = request.GET.get("status", "").strip()
    date_from = parse_date(request.GET.get("date_from", ""))
    date_to = parse_date(request.GET.get("date_to", ""))

    qs = get_application_list_queryset(demo_user)
    if status:
        qs = qs.filter(status=status)
    if date_from:
        qs = qs.filter(formed_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(formed_at__date__lte=date_to)

    return render(
        request,
        "applications.html",
        {
            "applications": qs,
            "statuses": Application.Status.choices,
            "selected_status": status,
            "date_from": request.GET.get("date_from", ""),
            "date_to": request.GET.get("date_to", ""),
            "selectedStatus": status,
            "dateFrom": request.GET.get("date_from", ""),
            "dateTo": request.GET.get("date_to", ""),
        },
    )


def application_detail(request, id):
    demo_user = get_constant_creator()
    app = Application.objects.filter(pk=id, creator=demo_user).select_related("applicant").first()
    if not app:
        raise Http404("Application not found")

    profile = get_or_create_profile(demo_user)

    if request.method == "POST":
        if app.applicant_id is None:
            app.applicant = profile
            app.save(update_fields=["applicant"])

        profile.full_name = request.POST.get("full_name", profile.full_name).strip()
        profile.phone = request.POST.get("phone", profile.phone).strip()
        profile.city = request.POST.get("city", profile.city).strip()

        age_raw = request.POST.get("age", "").strip()
        profile.age = int(age_raw) if age_raw.isdigit() else None

        gender = request.POST.get("gender", profile.gender)
        if gender in dict(ApplicantProfile.Gender.choices):
            profile.gender = gender

        disability_category = request.POST.get("disability_category", profile.disability_category)
        if disability_category in dict(ApplicantProfile.DisabilityCategory.choices):
            profile.disability_category = disability_category

        profile.save()

        for line in app.lines.all():
            key = f"comment_{line.id}"
            if key in request.POST:
                line.comment = (request.POST.get(key, "") or "").strip()
                line.save(update_fields=["comment"])

        recalc_application_sum(app)
        new_status = (request.POST.get("status") or "").strip()
        apply_status_change(app, new_status)
        return redirect("application", id=app.id)

    return render(request, "application.html", build_application_context(app, profile))


def add_to_application(request, id):
    demo_user = get_constant_creator()
    if request.method != "POST":
        return redirect("vacancies")

    vacancy = Vacancy.objects.filter(pk=id, is_active=True).first()
    if not vacancy:
        raise Http404("Vacancy not found")

    app = ensure_draft_application(demo_user)
    line = app.lines.filter(vacancy=vacancy).first()
    if not line:
        ApplicationVacancy.objects.create(
            application=app,
            vacancy=vacancy,
            qty=1,
            order_index=(
                app.lines.order_by("-order_index").values_list("order_index", flat=True).first()
                or 0
            )
            + 1,
            is_main=False,
            comment="",
        )

    recalc_application_sum(app)
    return redirect("vacancies")


def delete_application(request, id):
    demo_user = get_constant_creator()
    if request.method != "POST":
        return redirect("applications")

    app = Application.objects.filter(pk=id, creator=demo_user).first()
    if not app:
        raise Http404("Application not found")

    apply_status_change(app, Application.Status.DELETED)
    return redirect("applications")
