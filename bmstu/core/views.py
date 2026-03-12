from datetime import datetime

from django.contrib.auth.models import User
 
from django.db.models import Count, F, Max, Q, Sum
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import ApplicantProfile, Application, ApplicationVacancy, Vacancy


def _get_demo_user() -> User:
    user, _ = User.objects.get_or_create(username="demo")
    return user


def home_redirect(request):
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
    total = (
        ApplicationVacancy.objects.filter(application=app)
        .select_related("vacancy")
        .aggregate(
            s=Sum(F("qty") * F("vacancy__salary"))
        )
        .get("s")
        or 0
    )
    app.total_salary = int(total)
    app.save(update_fields=["total_salary"])
    return int(total)


#  Вакансии 
def VacanciesList(request):
    demo_user = _get_demo_user()
    search = request.GET.get("search", "").strip()

    qs = Vacancy.objects.filter(is_active=True)
    if search:
        qs = qs.filter(
            Q(title__icontains=search)
            | Q(company__icontains=search)
            | Q(city__icontains=search)
        )

    # текущая заявка 
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
        },
    )


#  Детальная вакансия
def VacancyDetail(request, id):
    vacancy = Vacancy.objects.filter(pk=id, is_active=True).first()
    if not vacancy:
        raise Http404("Vacancy not found")
    return render(request, "vacancy.html", {"vacancy": vacancy})


#  Список заявок 
def ApplicationsList(request):
    demo_user = _get_demo_user()

    status = request.GET.get("status", "").strip()
    date_from = _parse_date(request.GET.get("date_from", ""))
    date_to = _parse_date(request.GET.get("date_to", ""))

    qs = (
        Application.objects.filter(creator=demo_user)
        .annotate(
            lines_count=Coalesce(Count("applicationvacancy", distinct=True), 0),
            total_sum=Coalesce(
                Sum(F("applicationvacancy__qty") * F("applicationvacancy__vacancy__salary")),
                0,
            ),
        )
        .order_by("-id")
    )

    if status:
        qs = qs.filter(status=status)

    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    return render(
        request,
        "applications.html",
        {
            "applications": qs,
            "statuses": Application.Status.choices,
            "selected_status": status,
            "date_from": request.GET.get("date_from", ""),
            "date_to": request.GET.get("date_to", ""),
        },
    )


#  Заявка 
def ApplicationDetail(request, id):
    demo_user = _get_demo_user()

    app = Application.objects.filter(pk=id, creator=demo_user).first()
    if not app:
        raise Http404("Application not found")

    profile = _get_or_create_profile(demo_user)

    
    if app.applicant_id is None:
        app.applicant = profile
        app.save(update_fields=["applicant"])

    # POST: сохранить профиль + статус + комментарии
    if request.method == "POST":
        # статус заявки
        new_status = (request.POST.get("status") or "").strip()
        allowed_statuses = dict(Application.Status.choices)

        if new_status and new_status in allowed_statuses and new_status != app.status:
            now = timezone.now()
            app.status = new_status

            
            if new_status == Application.Status.FORMED and not app.formed_at:
                app.formed_at = now
            if new_status == Application.Status.FINISHED and not app.completed_at:
                
                if not app.formed_at:
                    app.formed_at = now
                app.completed_at = now
            if new_status == Application.Status.DELETED and not app.completed_at:
                app.completed_at = now

            app.save(update_fields=["status", "formed_at", "completed_at"])

        # профиль
        profile.full_name = request.POST.get("full_name", profile.full_name).strip()
        profile.phone = request.POST.get("phone", profile.phone).strip()
        profile.city = request.POST.get("city", profile.city).strip()

        age_raw = request.POST.get("age", "").strip()
        profile.age = int(age_raw) if age_raw.isdigit() else None

        gender = request.POST.get("gender", profile.gender)
        if gender in dict(ApplicantProfile.Gender.choices):
            profile.gender = gender

        cat = request.POST.get("disability_category", profile.disability_category)
        if cat in dict(ApplicantProfile.DisabilityCategory.choices):
            profile.disability_category = cat

        profile.save()

        # комментарии строк
        lines = ApplicationVacancy.objects.filter(application=app)
        for line in lines:
            key = f"comment_{line.id}"
            if key in request.POST:
                line.comment = (request.POST.get(key, "") or "").strip()
                line.save(update_fields=["comment"])

        _recalc_application_sum(app)
        return redirect("application", id=app.id)

    lines = (
        ApplicationVacancy.objects.filter(application=app)
        .select_related("vacancy")
        .order_by("order_index", "id")
    )

    total_positions = lines.count()
    total_sum = _recalc_application_sum(app)

    return render(
        request,
        "application.html",
        {
            "app": app,
            "profile": profile,
            "lines": lines,
            "total_positions": total_positions,
            "total_sum": total_sum,
            "status_choices": Application.Status.choices,
            "gender_choices": ApplicantProfile.Gender.choices,
            "category_choices": ApplicantProfile.DisabilityCategory.choices,
        },
    )


# POST: добавить вакансию в черновик
def add_to_application(request, id):
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


# POST: лог удал заявки через SQL
def delete_application(request, id):
    demo_user = _get_demo_user()

    if request.method != "POST":
        return redirect("applications")

    app = Application.objects.filter(pk=id, creator=demo_user).first()
    if not app:
        raise Http404("Application not found")

    now = timezone.now()
    Application.objects.filter(pk=id, creator=demo_user).update(
        status=Application.Status.DELETED,
        completed_at=Coalesce(F("completed_at"), now),
    )

    return redirect("applications")
