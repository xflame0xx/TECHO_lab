from datetime import datetime

from django.contrib.auth.models import User
from django.db.models import Count, ExpressionWrapper, F, IntegerField, Max, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from .Models import ApplicantProfile, Application, ApplicationVacancy

CREATOR_USERNAME = "creator_demo"
MODERATOR_USERNAME = "moderator_demo"


class SingletonUsers:
    _creator = None
    _moderator = None


def get_constant_creator() -> User:
    cached = SingletonUsers._creator
    if cached is not None and User.objects.filter(pk=cached.pk).exists():
        return cached

    SingletonUsers._creator, _ = User.objects.get_or_create(
        username=CREATOR_USERNAME,
        defaults={
            "first_name": "Demo",
            "last_name": "Creator",
            "email": "creator_demo@example.com",
        },
    )
    return SingletonUsers._creator


def get_constant_moderator() -> User:
    cached = SingletonUsers._moderator
    if cached is not None and User.objects.filter(pk=cached.pk).exists():
        return cached

    SingletonUsers._moderator, _ = User.objects.get_or_create(
        username=MODERATOR_USERNAME,
        defaults={
            "first_name": "Demo",
            "last_name": "Moderator",
            "email": "moderator_demo@example.com",
        },
    )
    return SingletonUsers._moderator


def parse_date(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


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


def recalc_application_sum(app: Application) -> int:
    total = 0
    for line in app.lines.select_related("vacancy"):
        total += line.qty * line.vacancy.salary
        if line.line_salary_total != line.qty * line.vacancy.salary:
            line.line_salary_total = line.qty * line.vacancy.salary
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
        if moderator is not None:
            app.moderator = moderator
            update_fields.append("moderator")
        update_fields.append("completed_at")

    if new_status == Application.Status.DELETED:
        app.completed_at = now
        update_fields.append("completed_at")

    app.save(update_fields=update_fields)
    return True


def get_application_list_queryset(creator: User):
    line_total = ExpressionWrapper(
        F("lines__qty") * F("lines__vacancy__salary"),
        output_field=IntegerField(),
    )
    return (
        Application.objects.filter(creator=creator)
        .exclude(status__in=[Application.Status.DELETED, Application.Status.DRAFT])
        .select_related("creator", "moderator", "applicant")
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


def ensure_draft_application(creator: User) -> Application:
    draft = Application.objects.filter(creator=creator, status=Application.Status.DRAFT).first()
    if draft:
        return draft

    profile = get_or_create_profile(creator)
    return Application.objects.create(
        creator=creator,
        applicant=profile,
        status=Application.Status.DRAFT,
    )


def next_order_index(application: Application) -> int:
    return (
        ApplicationVacancy.objects.filter(application=application)
        .aggregate(m=Max("order_index"))
        .get("m")
        or 0
    ) + 1
