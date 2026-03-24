from datetime import datetime

from django.contrib.auth.models import User
from django.db.models import Count, F, Max, Q, Sum
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from .Models import ApplicantProfile, Application, ApplicationVacancy, Vacancy


def _getDemoUser() -> User:
    user, _ = User.objects.get_or_create(username="demo")
    return user


def homeRedirect(request):
    return redirect("vacancies")


def _parseDate(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _getOrCreateProfile(user: User) -> ApplicantProfile:
    profile = getattr(user, "applicant_profile", None)
    if profile:
        return profile

    return ApplicantProfile.objects.create(
        user=user,
        full_name=user.get_full_name() or user.username,
        phone="",
        city="",
    )


def _recalcApplicationSum(app: Application) -> int:
    total = (
        ApplicationVacancy.objects.filter(application=app)
        .select_related("vacancy")
        .aggregate(s=Sum(F("qty") * F("vacancy__salary")))
        .get("s")
        or 0
    )
    app.total_salary = int(total)
    app.save(update_fields=["total_salary"])
    return int(total)


def vacanciesList(request):
    demoUser = _getDemoUser()
    search = request.GET.get("search", "").strip()

    qs = Vacancy.objects.filter(is_active=True)
    if search:
        qs = qs.filter(
            Q(title__icontains=search) | Q(company__icontains=search) | Q(city__icontains=search)
        )

    draft = Application.objects.filter(
        creator=demoUser,
        status=Application.Status.DRAFT,
    ).first()

    draftCount = 0
    if draft:
        draftCount = ApplicationVacancy.objects.filter(application=draft).count()

    return render(
        request,
        "vacancies.html",
        {
            "vacancies": qs.order_by("id"),
            "search": search,
            "draft": draft,
            "draftCount": draftCount,
        },
    )


def vacancyDetail(request, id):
    vacancy = Vacancy.objects.filter(pk=id, is_active=True).first()
    if not vacancy:
        raise Http404("Vacancy not found")
    return render(request, "vacancy.html", {"vacancy": vacancy})


def applicationsList(request):
    demoUser = _getDemoUser()

    status = request.GET.get("status", "").strip()
    dateFrom = _parseDate(request.GET.get("date_from", ""))
    dateTo = _parseDate(request.GET.get("date_to", ""))

    qs = (
        Application.objects.filter(creator=demoUser)
        .annotate(
            linesCount=Coalesce(Count("applicationvacancy", distinct=True), 0),
            totalSum=Coalesce(
                Sum(F("applicationvacancy__qty") * F("applicationvacancy__vacancy__salary")),
                0,
            ),
        )
        .order_by("-id")
    )

    if status:
        qs = qs.filter(status=status)

    if dateFrom:
        qs = qs.filter(created_at__date__gte=dateFrom)
    if dateTo:
        qs = qs.filter(created_at__date__lte=dateTo)

    return render(
        request,
        "applications.html",
        {
            "applications": qs,
            "statuses": Application.Status.choices,
            "selectedStatus": status,
            "dateFrom": request.GET.get("date_from", ""),
            "dateTo": request.GET.get("date_to", ""),
        },
    )


def applicationDetail(request, id):
    demoUser = _getDemoUser()

    app = Application.objects.filter(pk=id, creator=demoUser).first()
    if not app:
        raise Http404("Application not found")

    profile = _getOrCreateProfile(demoUser)

    if app.applicant_id is None:
        app.applicant = profile
        app.save(update_fields=["applicant"])

    if request.method == "POST":
        newStatus = (request.POST.get("status") or "").strip()
        allowedStatuses = dict(Application.Status.choices)

        if newStatus and newStatus in allowedStatuses and newStatus != app.status:
            now = timezone.now()
            app.status = newStatus

            if newStatus == Application.Status.FORMED and not app.formed_at:
                app.formed_at = now

            if newStatus == Application.Status.FINISHED and not app.completed_at:
                if not app.formed_at:
                    app.formed_at = now
                app.completed_at = now

            if newStatus == Application.Status.DELETED and not app.completed_at:
                app.completed_at = now

            app.save(update_fields=["status", "formed_at", "completed_at"])

        profile.full_name = request.POST.get("full_name", profile.full_name).strip()
        profile.phone = request.POST.get("phone", profile.phone).strip()
        profile.city = request.POST.get("city", profile.city).strip()

        ageRaw = request.POST.get("age", "").strip()
        profile.age = int(ageRaw) if ageRaw.isdigit() else None

        gender = request.POST.get("gender", profile.gender)
        if gender in dict(ApplicantProfile.Gender.choices):
            profile.gender = gender

        disabilityCategory = request.POST.get(
            "disability_category",
            profile.disability_category,
        )
        if disabilityCategory in dict(ApplicantProfile.DisabilityCategory.choices):
            profile.disability_category = disabilityCategory

        profile.save()

        lines = ApplicationVacancy.objects.filter(application=app)
        for line in lines:
            key = f"comment_{line.id}"
            if key in request.POST:
                line.comment = (request.POST.get(key, "") or "").strip()
                line.save(update_fields=["comment"])

        _recalcApplicationSum(app)
        return redirect("application", id=app.id)

    lines = (
        ApplicationVacancy.objects.filter(application=app)
        .select_related("vacancy")
        .order_by("order_index", "id")
    )

    totalPositions = lines.count()
    totalSum = _recalcApplicationSum(app)

    return render(
        request,
        "application.html",
        {
            "app": app,
            "profile": profile,
            "lines": lines,
            "totalPositions": totalPositions,
            "totalSum": totalSum,
            "statusChoices": Application.Status.choices,
            "genderChoices": ApplicantProfile.Gender.choices,
            "categoryChoices": ApplicantProfile.DisabilityCategory.choices,
        },
    )


def addToApplication(request, id):
    demoUser = _getDemoUser()

    if request.method != "POST":
        return redirect("vacancies")

    vacancy = Vacancy.objects.filter(pk=id, is_active=True).first()
    if not vacancy:
        raise Http404("Vacancy not found")

    app = Application.objects.filter(
        creator=demoUser,
        status=Application.Status.DRAFT,
    ).first()

    if not app:
        app = Application.objects.create(
            creator=demoUser,
            status=Application.Status.DRAFT,
        )

    profile = _getOrCreateProfile(demoUser)
    if app.applicant_id is None:
        app.applicant = profile
        app.save(update_fields=["applicant"])

    line = ApplicationVacancy.objects.filter(application=app, vacancy=vacancy).first()
    if not line:
        lastIdx = (
            ApplicationVacancy.objects.filter(application=app)
            .aggregate(m=Max("order_index"))
            .get("m")
            or 0
        )
        ApplicationVacancy.objects.create(
            application=app,
            vacancy=vacancy,
            qty=1,
            order_index=lastIdx + 1,
            is_main=False,
            comment="",
        )

    _recalcApplicationSum(app)
    return redirect("vacancies")


def deleteApplication(request, id):
    demoUser = _getDemoUser()

    if request.method != "POST":
        return redirect("applications")

    app = Application.objects.filter(pk=id, creator=demoUser).first()
    if not app:
        raise Http404("Application not found")

    now = timezone.now()
    Application.objects.filter(pk=id, creator=demoUser).update(
        status=Application.Status.DELETED,
        completed_at=Coalesce(F("completed_at"), now),
    )

    return redirect("applications")
