from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .api_serializers import RegisterSerializer
from .Models import ApplicantProfile, Application, ApplicationVacancy, UserAccount, Vacancy
from .services import (
    apply_status_change,
    approve_vacancy,
    ensure_demo_moderator,
    ensure_draft_application,
    get_application_list_queryset,
    get_employer_applications_queryset,
    get_or_create_profile,
    get_public_vacancies_queryset,
    get_user_role,
    next_order_index,
    parse_date,
    recalc_application_sum,
    reject_vacancy,
)


def require_role(request, *roles):
    if not request.user.is_authenticated:
        return redirect("login")
    if get_user_role(request.user) not in set(roles):
        raise PermissionDenied("Недостаточно прав")
    return None


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("vacancies")


@login_required
def dashboard_redirect(request):
    role = get_user_role(request.user)
    if role == UserAccount.Role.EMPLOYER:
        return redirect("employer_cabinet")
    if role == UserAccount.Role.MODERATOR:
        return redirect("moderator_cabinet")
    return redirect("applicant_cabinet")


def register_view(request):
    ensure_demo_moderator()

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        payload = {
            "username": (request.POST.get("username") or "").strip(),
            "password": request.POST.get("password") or "",
            "first_name": (request.POST.get("first_name") or "").strip(),
            "last_name": (request.POST.get("last_name") or "").strip(),
            "email": (request.POST.get("email") or "").strip(),
            "role": (request.POST.get("role") or UserAccount.Role.APPLICANT).strip(),
        }

        serializer = RegisterSerializer(data=payload)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            messages.success(request, "Аккаунт создан. Добро пожаловать в JobAbility.")
            return redirect("dashboard")

        return render(
            request,
            "auth/register.html",
            {
                "errors": serializer.errors,
                "form": payload,
            },
        )

    return render(request, "auth/register.html", {"form": {}})


def login_view(request):
    ensure_demo_moderator()

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        selected_role = (request.POST.get("role") or "").strip()

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Неверный логин или пароль.")
        elif selected_role and get_user_role(user) != selected_role:
            messages.error(request, "Выбранная роль не соответствует этому аккаунту.")
        else:
            login(request, user)
            messages.success(request, "Вход выполнен успешно.")
            return redirect("dashboard")

    return render(
        request,
        "auth/login.html",
        {
            "demo_moderator": {"username": "moderator_demo", "password": "moderator123"},
        },
    )


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Вы вышли из системы.")
    return redirect("login")


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
    search = request.GET.get("search", "").strip()

    qs = get_public_vacancies_queryset()
    if search:
        qs = qs.filter(
            Q(title__icontains=search) | Q(company__icontains=search) | Q(city__icontains=search)
        )

    draft = None
    draft_count = 0
    if request.user.is_authenticated and get_user_role(request.user) == UserAccount.Role.APPLICANT:
        draft = Application.objects.filter(
            creator=request.user,
            status=Application.Status.DRAFT,
        ).first()
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
    vacancy = get_object_or_404(
        Vacancy,
        pk=id,
        is_active=True,
        moderation_status=Vacancy.ModerationStatus.APPROVED,
    )
    return render(request, "vacancy.html", {"vacancy": vacancy})


def applications_list(request):
    gate = require_role(request, UserAccount.Role.APPLICANT, UserAccount.Role.MODERATOR)
    if gate:
        return gate

    status = request.GET.get("status", "").strip()
    date_from = parse_date(request.GET.get("date_from", ""))
    date_to = parse_date(request.GET.get("date_to", ""))

    qs = get_application_list_queryset(request.user)
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
    gate = require_role(request, UserAccount.Role.APPLICANT)
    if gate:
        return gate

    app = (
        Application.objects.filter(pk=id, creator=request.user).select_related("applicant").first()
    )
    if not app:
        raise Http404("Application not found")

    profile = get_or_create_profile(request.user)

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

        messages.success(request, "Заявка обновлена.")
        return redirect("application", id=app.id)

    return render(request, "application.html", build_application_context(app, profile))


def add_to_application(request, id):
    gate = require_role(request, UserAccount.Role.APPLICANT)
    if gate:
        return gate

    if request.method != "POST":
        return redirect("vacancies")

    vacancy = Vacancy.objects.filter(
        pk=id,
        is_active=True,
        moderation_status=Vacancy.ModerationStatus.APPROVED,
    ).first()
    if not vacancy:
        raise Http404("Vacancy not found")

    app = ensure_draft_application(request.user)
    line = app.lines.filter(vacancy=vacancy).first()
    if not line:
        ApplicationVacancy.objects.create(
            application=app,
            vacancy=vacancy,
            qty=1,
            order_index=next_order_index(app),
            is_main=False,
            comment="",
        )

    recalc_application_sum(app)
    messages.success(request, "Вакансия добавлена в заявку.")
    return redirect("vacancies")


def delete_application(request, id):
    gate = require_role(request, UserAccount.Role.APPLICANT)
    if gate:
        return gate

    if request.method != "POST":
        return redirect("applications")

    app = Application.objects.filter(pk=id, creator=request.user).first()
    if not app:
        raise Http404("Application not found")

    apply_status_change(app, Application.Status.DELETED)
    messages.success(request, "Заявка удалена.")
    return redirect("applications")


def applicant_cabinet(request):
    gate = require_role(request, UserAccount.Role.APPLICANT)
    if gate:
        return gate

    profile = get_or_create_profile(request.user)

    if request.method == "POST":
        profile.full_name = (request.POST.get("full_name") or "").strip()
        profile.phone = (request.POST.get("phone") or "").strip()
        profile.city = (request.POST.get("city") or "").strip()

        age_raw = (request.POST.get("age") or "").strip()
        profile.age = int(age_raw) if age_raw.isdigit() else None

        gender = request.POST.get("gender", profile.gender)
        if gender in dict(ApplicantProfile.Gender.choices):
            profile.gender = gender

        disability_category = request.POST.get("disability_category", profile.disability_category)
        if disability_category in dict(ApplicantProfile.DisabilityCategory.choices):
            profile.disability_category = disability_category

        profile.save()
        messages.success(request, "Профиль сохранён.")
        return redirect("applicant_cabinet")

    last_applications = (
        Application.objects.filter(creator=request.user)
        .exclude(status=Application.Status.DELETED)
        .order_by("-id")[:5]
    )
    draft = Application.objects.filter(
        creator=request.user, status=Application.Status.DRAFT
    ).first()

    return render(
        request,
        "cabinet/applicant.html",
        {
            "profile": profile,
            "last_applications": last_applications,
            "draft": draft,
            "gender_choices": ApplicantProfile.Gender.choices,
            "category_choices": ApplicantProfile.DisabilityCategory.choices,
        },
    )


def employer_cabinet(request):
    gate = require_role(request, UserAccount.Role.EMPLOYER)
    if gate:
        return gate

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        company = (request.POST.get("company") or "").strip()
        city = (request.POST.get("city") or "").strip()
        description = (request.POST.get("description") or "").strip()
        schedule = (request.POST.get("schedule") or "").strip()
        disability_support = (request.POST.get("disability_support") or "").strip()
        salary_raw = (request.POST.get("salary") or "0").strip()

        salary = int(salary_raw) if salary_raw.isdigit() else 0

        Vacancy.objects.create(
            title=title,
            company=company,
            city=city,
            description=description,
            schedule=schedule,
            disability_support=disability_support,
            salary=salary,
            creator=request.user,
            moderation_status=Vacancy.ModerationStatus.PENDING,
            is_active=False,
            image=request.FILES.get("image"),
            video=request.FILES.get("video"),
        )
        messages.success(request, "Вакансия отправлена на модерацию.")
        return redirect("employer_cabinet")

    vacancies = Vacancy.objects.filter(creator=request.user).order_by("-id")
    return render(
        request,
        "cabinet/employer.html",
        {
            "vacancies": vacancies,
        },
    )


def employer_responses(request):
    gate = require_role(request, UserAccount.Role.EMPLOYER)
    if gate:
        return gate

    applications = get_employer_applications_queryset(request.user)
    return render(
        request,
        "cabinet/employer_responses.html",
        {
            "applications": applications,
        },
    )


def moderator_cabinet(request):
    gate = require_role(request, UserAccount.Role.MODERATOR)
    if gate:
        return gate

    if request.method == "POST":
        entity = (request.POST.get("entity") or "").strip()
        object_id = (request.POST.get("object_id") or "").strip()
        action = (request.POST.get("action") or "").strip()
        note = (request.POST.get("moderation_note") or "").strip()

        if object_id.isdigit():
            if entity == "vacancy":
                vacancy = get_object_or_404(Vacancy, pk=int(object_id))
                if action == "approve":
                    approve_vacancy(vacancy, request.user, note)
                    messages.success(request, f"Вакансия #{vacancy.id} одобрена.")
                elif action == "reject":
                    reject_vacancy(vacancy, request.user, note)
                    messages.warning(request, f"Вакансия #{vacancy.id} отклонена.")

            if entity == "application":
                app = get_object_or_404(Application, pk=int(object_id))
                if app.status == Application.Status.FORMED:
                    app.moderator_note = note
                    app.save(update_fields=["moderator_note"])

                    if action == "finish":
                        apply_status_change(
                            app, Application.Status.FINISHED, moderator=request.user
                        )
                        messages.success(request, f"Заявка #{app.id} завершена.")
                    elif action == "reject":
                        apply_status_change(
                            app, Application.Status.REJECTED, moderator=request.user
                        )
                        messages.warning(request, f"Заявка #{app.id} отклонена.")

        return redirect("moderator_cabinet")

    pending_vacancies = (
        Vacancy.objects.filter(moderation_status=Vacancy.ModerationStatus.PENDING)
        .select_related("creator")
        .order_by("-id")
    )

    formed_applications = (
        Application.objects.filter(status=Application.Status.FORMED)
        .select_related("creator", "applicant")
        .prefetch_related("lines__vacancy")
        .order_by("-id")
    )

    return render(
        request,
        "cabinet/moderator.html",
        {
            "pending_vacancies": pending_vacancies,
            "formed_applications": formed_applications,
        },
    )
