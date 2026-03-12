from django.contrib.auth.models import User
from django.db import models


class Vacancy(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    salary = models.IntegerField(default=0)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to="vacancies/", blank=True, null=True)

    disability_support = models.CharField(max_length=255, blank=True, default="")
    schedule = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"{self.title} ({self.company})"


class ApplicantProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Мужчина"
        FEMALE = "female", "Женщина"
        OTHER = "other", "Другое"

    class DisabilityCategory(models.TextChoices):
        NONE = "none", "Нет"
        I = "I", "I группа"
        II = "II", "II группа"
        III = "III", "III группа"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="applicant_profile",
    )

    full_name = models.CharField("ФИО", max_length=255, blank=True, default="")
    phone = models.CharField("Телефон", max_length=64, blank=True, default="")
    city = models.CharField("Город", max_length=255, blank=True, default="")

    age = models.IntegerField("Возраст", blank=True, null=True)

    gender = models.CharField(
        "Пол",
        max_length=16,
        choices=Gender.choices,
        default=Gender.OTHER,
    )

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
        DELETED = "DELETED", "Удалена"

    creator = models.ForeignKey(User, on_delete=models.CASCADE)
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

    total_salary = models.IntegerField(default=0)

    def __str__(self):
        return f"Заявка #{self.id}"


class ApplicationVacancy(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE)

    qty = models.IntegerField(default=1)

    comment = models.TextField(blank=True, null=True, default="")

    is_main = models.BooleanField(default=False)
    order_index = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.application_id} -> {self.vacancy_id}"