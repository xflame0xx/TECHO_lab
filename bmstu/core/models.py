import os
import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone

CYRILLIC_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def transliterate_to_latin(value: str) -> str:
    value = (value or "").strip()
    chars = []
    for ch in value:
        lower = ch.lower()
        if lower in CYRILLIC_TO_LATIN:
            latin = CYRILLIC_TO_LATIN[lower]
            chars.append(latin.upper() if ch.isupper() else latin)
        else:
            chars.append(ch)
    transliterated = "".join(chars)
    slug = slugify(transliterated)
    return slug or "file"


def build_upload_path(prefix: str, instance, filename: str) -> str:
    base_name, extension = os.path.splitext(filename or "")
    extension = extension.lower() or ".bin"
    source_name = getattr(instance, "title", "") or base_name or "file"
    normalized = transliterate_to_latin(source_name)
    suffix = uuid.uuid4().hex[:12]
    return f"{prefix}/{normalized}-{suffix}{extension}"


def vacancy_image_upload_to(instance, filename: str) -> str:
    return build_upload_path("vacancies/images", instance, filename)


def vacancy_video_upload_to(instance, filename: str) -> str:
    return build_upload_path("vacancies/videos", instance, filename)


class UserAccount(models.Model):
    class Role(models.TextChoices):
        APPLICANT = "applicant", "Соискатель"
        EMPLOYER = "employer", "Работодатель"
        MODERATOR = "moderator", "Модератор"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="account")
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.APPLICANT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class Vacancy(models.Model):
    class ModerationStatus(models.TextChoices):
        PENDING = "PENDING", "На модерации"
        APPROVED = "APPROVED", "Одобрена"
        REJECTED = "REJECTED", "Отклонена"

    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    salary = models.IntegerField(default=0)
    description = models.TextField(blank=True)

    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="created_vacancies",
        null=True,
        blank=True,
    )
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="moderated_vacancies",
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)
    moderation_status = models.CharField(
        max_length=16,
        choices=ModerationStatus.choices,
        default=ModerationStatus.APPROVED,
    )
    moderation_note = models.TextField(blank=True, default="")
    published_at = models.DateTimeField(blank=True, null=True)

    image = models.ImageField(upload_to=vacancy_image_upload_to, blank=True, null=True)
    video = models.FileField(upload_to=vacancy_video_upload_to, blank=True, null=True)

    disability_support = models.CharField(max_length=255, blank=True, default="")
    schedule = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"{self.title} ({self.company})"

    @property
    def is_published(self) -> bool:
        return self.is_active and self.moderation_status == self.ModerationStatus.APPROVED


class ApplicantProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Мужчина"
        FEMALE = "female", "Женщина"
        OTHER = "other", "Другое"

    class DisabilityCategory(models.TextChoices):
        NONE = "none", "Нет"
        GROUP_I = "I", "I группа"
        GROUP_II = "II", "II группа"
        GROUP_III = "III", "III группа"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="applicant_profile")
    full_name = models.CharField("ФИО", max_length=255, blank=True, default="")
    phone = models.CharField("Телефон", max_length=64, blank=True, default="")
    city = models.CharField("Город", max_length=255, blank=True, default="")
    age = models.IntegerField("Возраст", blank=True, null=True)
    gender = models.CharField("Пол", max_length=16, choices=Gender.choices, default=Gender.OTHER)
    disability_category = models.CharField(
        "Категория инвалидности",
        max_length=16,
        choices=DisabilityCategory.choices,
        default=DisabilityCategory.NONE,
    )

    def __str__(self):
        return self.full_name or self.user.username


class Application(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Черновик"
        FORMED = "FORMED", "Сформирована"
        FINISHED = "FINISHED", "Завершена"
        REJECTED = "REJECTED", "Отклонена"
        DELETED = "DELETED", "Удалена"

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_applications")
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="moderated_applications",
        null=True,
        blank=True,
    )
    applicant = models.ForeignKey(
        ApplicantProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
    )

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    formed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    contact_email = models.EmailField(blank=True, default="")
    cover_letter = models.TextField(blank=True, default="")
    estimated_response_date = models.DateField(blank=True, null=True)
    moderator_note = models.TextField(blank=True, default="")
    total_salary = models.IntegerField(default=0)

    def __str__(self):
        return f"Заявка #{self.id}"

    def recalculate_total_salary(self) -> int:
        total = sum(
            (line.line_salary_total or line.qty * line.vacancy.salary)
            for line in self.lines.select_related("vacancy")
        )
        self.total_salary = int(total)
        self.save(update_fields=["total_salary"])
        return int(total)

    def calculate_estimated_response_date(self):
        base = self.formed_at or timezone.now()
        delay_days = min(30, max(1, self.lines.count()) * 3)
        return (base + timedelta(days=delay_days)).date()


class ApplicationVacancy(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="lines")
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="application_lines")
    qty = models.IntegerField(default=1)
    comment = models.TextField(blank=True, null=True, default="")
    is_main = models.BooleanField(default=False)
    order_index = models.IntegerField(default=1)
    line_salary_total = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ("order_index", "id")
        unique_together = ("application", "vacancy")

    def __str__(self):
        return f"{self.application_id} -> {self.vacancy_id}"

    def recalculate_result(self) -> int:
        self.line_salary_total = int(self.qty * self.vacancy.salary)
        self.save(update_fields=["line_salary_total"])
        return self.line_salary_total
