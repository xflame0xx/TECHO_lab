from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Count, ExpressionWrapper, F, IntegerField, Max, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from .Models import ApplicantProfile, Application, UserAccount, Vacancy

User = get_user_model()

DEFAULT_MODERATOR_USERNAME = "Ilya Snytkin"
DEFAULT_MODERATOR_PASSWORD = "Ilya123"


def parse_date(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def ensure_user_account(user: User, role: str = UserAccount.Role.APPLICANT) -> UserAccount:
    account = getattr(user, "account", None)
    if account:
        if role and account.role != role:
            account.role = role
            account.save(update_fields=["role"])
        return account
    return UserAccount.objects.create(user=user, role=role)


def ensure_demo_moderator() -> User:
    user, created = User.objects.get_or_create(
        username=DEFAULT_MODERATOR_USERNAME,
        defaults={
            "first_name": "Demo",
            "last_name": "Moderator",
            "email": "moderator_demo@example.com",
            "is_staff": True,
        },
    )
    if created or not user.has_usable_password():
        user.set_password(DEFAULT_MODERATOR_PASSWORD)
        user.save(update_fields=["password"])
    ensure_user_account(user, UserAccount.Role.MODERATOR)
    return user


def get_user_role(user: User | None) -> str | None:
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    if getattr(user, "is_superuser", False):
        return UserAccount.Role.MODERATOR
    return getattr(getattr(user, "account", None), "role", None)


def user_has_role(user: User | None, *roles: str) -> bool:
    return get_user_role(user) in set(roles)


def get_or_create_profile(user: User) -> ApplicantProfile:
    profile = getattr(user, "applicant_profile", None)
    if profile:
        return profile

    return ApplicantProfile.objects.create(
        user=user,
        full_name=user.get_full_name() or user.username,
        phone="",
        city="",
    )


def get_public_vacancies_queryset():
    return Vacancy.objects.filter(
        is_active=True,
        moderation_status=Vacancy.ModerationStatus.APPROVED,
    ).select_related("creator", "moderator")


def recalc_application_sum(app: Application) -> int:
    total = 0
    for line in app.lines.select_related("vacancy"):
        current_total = line.qty * line.vacancy.salary
        total += current_total
        if line.line_salary_total != current_total:
            line.line_salary_total = current_total
            line.save(update_fields=["line_salary_total"])

    app.total_salary = int(total)
    app.save(update_fields=["total_salary"])
    return int(total)


def apply_status_change(app: Application, new_status: str, moderator: User | None = None) -> bool:
    if not new_status or new_status == app.status:
        return False

    allowed_transitions = {
        Application.Status.DRAFT: {Application.Status.FORMED, Application.Status.DELETED},
        Application.Status.FORMED: {Application.Status.FINISHED, Application.Status.REJECTED},
        Application.Status.FINISHED: set(),
        Application.Status.REJECTED: set(),
        Application.Status.DELETED: set(),
    }

    if new_status not in allowed_transitions.get(app.status, set()):
        return False

    now = timezone.now()
    update_fields = ["status"]
    app.status = new_status

    if new_status == Application.Status.FORMED:
        app.formed_at = now
        app.estimated_response_date = app.calculate_estimated_response_date()
        update_fields.extend(["formed_at", "estimated_response_date"])

    if new_status in {Application.Status.FINISHED, Application.Status.REJECTED}:
        app.completed_at = now
        update_fields.append("completed_at")
        if moderator is not None:
            app.moderator = moderator
            update_fields.append("moderator")

    app.save(update_fields=update_fields)
    return True


def ensure_draft_application(creator: User) -> Application:
    draft = Application.objects.filter(creator=creator, status=Application.Status.DRAFT).first()
    if draft:
        return draft

    profile = get_or_create_profile(creator)
    return Application.objects.create(
        creator=creator,
        applicant=profile,
        status=Application.Status.DRAFT,
        contact_email=creator.email,
    )


def next_order_index(app: Application) -> int:
    current_max = app.lines.aggregate(max_order=Max("order_index")).get("max_order") or 0
    return int(current_max) + 1


def get_application_list_queryset(user: User):
    line_total = ExpressionWrapper(
        F("lines__qty") * F("lines__vacancy__salary"),
        output_field=IntegerField(),
    )
    base_qs = Application.objects.exclude(status=Application.Status.DELETED)
    if user_has_role(user, UserAccount.Role.MODERATOR):
        qs = base_qs
    else:
        qs = base_qs.filter(creator=user)

    return (
        qs.select_related("creator", "moderator", "applicant")
        .annotate(
            lines_count=Coalesce(Count("lines", distinct=True), 0),
            calculated_lines_count=Coalesce(
                Count("lines", filter=Q(lines__line_salary_total__isnull=False), distinct=True),
                0,
            ),
            total_sum=Coalesce(Sum(line_total), 0),
        )
        .order_by("-id")
    )


def get_employer_applications_queryset(user: User):
    line_total = ExpressionWrapper(
        F("lines__qty") * F("lines__vacancy__salary"),
        output_field=IntegerField(),
    )
    return (
        Application.objects.filter(lines__vacancy__creator=user)
        .exclude(status=Application.Status.DELETED)
        .select_related("creator", "moderator", "applicant")
        .annotate(
            lines_count=Coalesce(Count("lines", distinct=True), 0),
            total_sum=Coalesce(Sum(line_total), 0),
        )
        .distinct()
        .order_by("-id")
    )


def approve_vacancy(vacancy: Vacancy, moderator: User, note: str = "") -> Vacancy:
    vacancy.moderator = moderator
    vacancy.moderation_note = note
    vacancy.moderation_status = Vacancy.ModerationStatus.APPROVED
    vacancy.is_active = True
    if vacancy.published_at is None:
        vacancy.published_at = timezone.now()
    vacancy.save(
        update_fields=[
            "moderator",
            "moderation_note",
            "moderation_status",
            "is_active",
            "published_at",
        ]
    )
    return vacancy


def reject_vacancy(vacancy: Vacancy, moderator: User, note: str = "") -> Vacancy:
    vacancy.moderator = moderator
    vacancy.moderation_note = note
    vacancy.moderation_status = Vacancy.ModerationStatus.REJECTED
    vacancy.is_active = False
    vacancy.save(update_fields=["moderator", "moderation_note", "moderation_status", "is_active"])
    return vacancy
