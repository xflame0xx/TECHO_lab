from datetime import datetime

from django.contrib.auth.models import User
from django.db.models import Count, ExpressionWrapper, F, IntegerField, Max, Q, Sum
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .Models import ApplicantProfile, Application, ApplicationVacancy, Vacancy


def _get_demo_user() -> User:
    user, _ = User.objects.get_or_create(
        username="demo",
        defaults={"first_name": "Demo"},
    )
    return user


def homeRedirect(request):
    return redirect("vacancies")


def _parse_date(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _get_or_create_profile(user: User) -> ApplicantProfile:
    profile = getattr(user, "applicant_profile", None)
    if profile:
        return profile

    return ApplicantProfile.objects.create(
        user=user,
        full_name=user.get_full_name() or user.username,
        phone="",
        city="",
    )


def _recalc_application_sum(app: Application) -> int:
    line_total = ExpressionWrapper(
        F("qty") * F("vacancy__salary"),
        output_field=IntegerField(),
    )

    total = (
        ApplicationVacancy.objects.filter(application=app)
        .select_related("vacancy")
        .aggregate(s=Coalesce(Sum(line_total), 0))
        .get("s")
        or 0
    )

    app.total_salary = int(total)
    app.save(update_fields=["total_salary"])
    return int(total)


def _apply_status_change(app: Application, new_status: str) -> bool:
    if not new_status or new_status == app.status:
        return False

    allowed_transitions = {
        Application.Status.DRAFT: {
            Application.Status.FORMED,
            Application.Status.DELETED,
        },
        Application.Status.FORMED: {
            Application.Status.FINISHED,
        },
        Application.Status.FINISHED: set(),
        Application.Status.DELETED: set(),
    }

    if new_status not in allowed_transitions.get(app.status, set()):
        return False

    now = timezone.now()
    update_fields = ["status"]
    app.status = new_status

    if new_status == Application.Status.FORMED and not app.formed_at:
        app.formed_at = now
        update_fields.append("formed_at")

    if new_status == Application.Status.FINISHED:
        if not app.formed_at:
            app.formed_at = now
            update_fields.append("formed_at")
        if not app.completed_at:
            app.completed_at = now
            update_fields.append("completed_at")

    if new_status == Application.Status.DELETED and not app.completed_at:
        app.completed_at = now
        update_fields.append("completed_at")

    app.save(update_fields=update_fields)
    return True


def _build_application_context(app: Application, profile: ApplicantProfile) -> dict:
    lines = (
        ApplicationVacancy.objects.filter(application=app)
        .select_related("vacancy")
        .order_by("order_index", "id")
    )

    total_positions = lines.count()
    total_sum = _recalc_application_sum(app)

    context = {
        "app": app,
        "profile": profile,
        "lines": lines,
        "total_positions": total_positions,
        "total_sum": total_sum,
        "status_choices": Application.Status.choices,
        "gender_choices": ApplicantProfile.Gender.choices,
        "category_choices": ApplicantProfile.DisabilityCategory.choices,
        # Для обратной совместимости с уже существующими шаблонами
        "totalPositions": total_positions,
        "totalSum": total_sum,
        "statusChoices": Application.Status.choices,
        "genderChoices": ApplicantProfile.Gender.choices,
        "categoryChoices": ApplicantProfile.DisabilityCategory.choices,
    }
    return context


def vacanciesList(request):
    demo_user = _get_demo_user()
    search = request.GET.get("search", "").strip()

    qs = Vacancy.objects.filter(is_active=True)
    if search:
        qs = qs.filter(
            Q(title__icontains=search) | Q(company__icontains=search) | Q(city__icontains=search)
        )

    draft = Application.objects.filter(
        creator=demo_user,
        status=Application.Status.DRAFT,
    ).first()

    draft_count = 0
    if draft:
        draft_count = ApplicationVacancy.objects.filter(application=draft).count()

    return render(
        request,
        "vacancies.html",
        {
            "vacancies": qs.order_by("id"),
            "search": search,
            "draft": draft,
            "draft_count": draft_count,
            # Обратная совместимость
            "draftCount": draft_count,
        },
    )


def vacancyDetail(request, id):
    vacancy = get_object_or_404(Vacancy, pk=id, is_active=True)
    return render(request, "vacancy.html", {"vacancy": vacancy})


def applicationsList(request):
    demo_user = _get_demo_user()

    status = request.GET.get("status", "").strip()
    date_from = _parse_date(request.GET.get("date_from", ""))
    date_to = _parse_date(request.GET.get("date_to", ""))

    line_total = ExpressionWrapper(
        F("lines__qty") * F("lines__vacancy__salary"),
        output_field=IntegerField(),
    )

    qs = (
        Application.objects.filter(creator=demo_user)
        .exclude(status=Application.Status.DELETED)
        .annotate(
            lines_count=Coalesce(Count("lines", distinct=True), 0),
            total_sum=Coalesce(Sum(line_total), 0),
        )
        .order_by("-id")
    )

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
            # Обратная совместимость
            "selectedStatus": status,
            "dateFrom": request.GET.get("date_from", ""),
            "dateTo": request.GET.get("date_to", ""),
        },
    )


def applicationDetail(request, id):
    demo_user = _get_demo_user()

    app = Application.objects.filter(pk=id, creator=demo_user).first()
    if not app:
        raise Http404("Application not found")

    profile = _get_or_create_profile(demo_user)

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

        disability_category = request.POST.get(
            "disability_category",
            profile.disability_category,
        )
        if disability_category in dict(ApplicantProfile.DisabilityCategory.choices):
            profile.disability_category = disability_category

        profile.save()

        lines = ApplicationVacancy.objects.filter(application=app)
        for line in lines:
            key = f"comment_{line.id}"
            if key in request.POST:
                line.comment = (request.POST.get(key, "") or "").strip()
                line.save(update_fields=["comment"])

        _recalc_application_sum(app)

        new_status = (request.POST.get("status") or "").strip()
        _apply_status_change(app, new_status)

        return redirect("application", id=app.id)

    context = _build_application_context(app, profile)
    return render(request, "application.html", context)


def addToApplication(request, id):
    demo_user = _get_demo_user()

    if request.method != "POST":
        return redirect("vacancies")

    vacancy = Vacancy.objects.filter(pk=id, is_active=True).first()
    if not vacancy:
        raise Http404("Vacancy not found")

    app = Application.objects.filter(
        creator=demo_user,
        status=Application.Status.DRAFT,
    ).first()

    if not app:
        app = Application.objects.create(
            creator=demo_user,
            status=Application.Status.DRAFT,
        )

    profile = _get_or_create_profile(demo_user)
    if app.applicant_id is None:
        app.applicant = profile
        app.save(update_fields=["applicant"])

    line = ApplicationVacancy.objects.filter(application=app, vacancy=vacancy).first()
    if not line:
        last_idx = (
            ApplicationVacancy.objects.filter(application=app)
            .aggregate(m=Max("order_index"))
            .get("m")
            or 0
        )
        ApplicationVacancy.objects.create(
            application=app,
            vacancy=vacancy,
            qty=1,
            order_index=last_idx + 1,
            is_main=False,
            comment="",
        )

    _recalc_application_sum(app)
    return redirect("vacancies")


def deleteApplication(request, id):
    demo_user = _get_demo_user()

    if request.method != "POST":
        return redirect("applications")

    app = Application.objects.filter(
        pk=id,
        creator=demo_user,
    ).first()
    if not app:
        raise Http404("Application not found")

    _apply_status_change(app, Application.Status.DELETED)
    return redirect("applications")
