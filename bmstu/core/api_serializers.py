from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .Models import ApplicantProfile, Application, ApplicationVacancy, UserAccount, Vacancy
from .services import (
    apply_status_change,
    get_or_create_profile,
    get_user_role,
    recalc_application_sum,
)

User = get_user_model()


class VacancySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    creator_login = serializers.CharField(source="creator.username", read_only=True)
    moderator_login = serializers.CharField(source="moderator.username", read_only=True)
    is_published = serializers.SerializerMethodField()

    class Meta:
        model = Vacancy
        fields = [
            "id",
            "title",
            "company",
            "city",
            "salary",
            "description",
            "is_active",
            "disability_support",
            "schedule",
            "image",
            "video",
            "image_url",
            "video_url",
            "creator_login",
            "moderator_login",
            "moderation_status",
            "moderation_note",
            "published_at",
            "is_published",
        ]
        read_only_fields = [
            "id",
            "image_url",
            "video_url",
            "creator_login",
            "moderator_login",
            "moderation_status",
            "moderation_note",
            "published_at",
            "is_published",
        ]

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

    def get_video_url(self, obj):
        return obj.video.url if obj.video else None

    def get_is_published(self, obj):
        return obj.is_published


class ApplicantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicantProfile
        fields = ["id", "full_name", "phone", "city", "age", "gender", "disability_category"]
        read_only_fields = ["id"]


class ApplicationLineSerializer(serializers.ModelSerializer):
    vacancy = VacancySerializer(read_only=True)
    vacancy_id = serializers.IntegerField(write_only=True, required=False)
    calculated_result = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationVacancy
        fields = [
            "id",
            "vacancy",
            "vacancy_id",
            "qty",
            "comment",
            "is_main",
            "order_index",
            "line_salary_total",
            "calculated_result",
        ]
        read_only_fields = ["id", "line_salary_total", "calculated_result"]

    def get_calculated_result(self, obj):
        return (
            obj.line_salary_total
            if obj.line_salary_total is not None
            else obj.qty * obj.vacancy.salary
        )


class ApplicationListSerializer(serializers.ModelSerializer):
    creator_login = serializers.CharField(source="creator.username", read_only=True)
    moderator_login = serializers.CharField(source="moderator.username", read_only=True)
    applicant_name = serializers.CharField(source="applicant.full_name", read_only=True)
    lines_count = serializers.IntegerField(read_only=True)
    calculated_lines_count = serializers.IntegerField(read_only=True)
    total_sum = serializers.IntegerField(read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "status",
            "creator_login",
            "moderator_login",
            "applicant_name",
            "created_at",
            "formed_at",
            "completed_at",
            "contact_email",
            "estimated_response_date",
            "total_salary",
            "lines_count",
            "calculated_lines_count",
            "total_sum",
        ]


class ApplicationDetailSerializer(serializers.ModelSerializer):
    creator_login = serializers.CharField(source="creator.username", read_only=True)
    moderator_login = serializers.CharField(source="moderator.username", read_only=True)
    applicant = ApplicantProfileSerializer(read_only=True)
    lines = ApplicationLineSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "status",
            "creator_login",
            "moderator_login",
            "created_at",
            "formed_at",
            "completed_at",
            "contact_email",
            "cover_letter",
            "estimated_response_date",
            "moderator_note",
            "total_salary",
            "applicant",
            "lines",
        ]


class ApplicationCartSerializer(serializers.Serializer):
    application_id = serializers.IntegerField(allow_null=True)
    items_count = serializers.IntegerField()


class ApplicationUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=64)
    city = serializers.CharField(required=False, allow_blank=True, max_length=255)
    age = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    gender = serializers.ChoiceField(required=False, choices=ApplicantProfile.Gender.choices)
    disability_category = serializers.ChoiceField(
        required=False, choices=ApplicantProfile.DisabilityCategory.choices
    )
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    cover_letter = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance: Application, validated_data):
        profile = instance.applicant or get_or_create_profile(instance.creator)
        instance.applicant = profile

        profile_fields = ["full_name", "phone", "city", "age", "gender", "disability_category"]
        profile_updated = False
        for field in profile_fields:
            if field in validated_data:
                setattr(profile, field, validated_data[field])
                profile_updated = True

        if profile_updated:
            profile.save()

        if "contact_email" in validated_data:
            instance.contact_email = validated_data["contact_email"]
        if "cover_letter" in validated_data:
            instance.cover_letter = validated_data["cover_letter"]

        instance.save()
        recalc_application_sum(instance)
        return instance

    def create(self, validated_data):
        raise NotImplementedError


class ApplicationFormSerializer(serializers.Serializer):
    def validate(self, attrs):
        app: Application = self.context["application"]
        profile = app.applicant or get_or_create_profile(app.creator)
        errors = {}

        if app.status != Application.Status.DRAFT:
            errors["status"] = "Сформировать можно только заявку в статусе черновика."
        if not app.lines.exists():
            errors["lines"] = "Нельзя сформировать пустую заявку."
        if not profile.full_name:
            errors["full_name"] = "Укажите ФИО заявителя."
        if not profile.phone:
            errors["phone"] = "Укажите телефон заявителя."
        if not profile.city:
            errors["city"] = "Укажите город заявителя."

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def save(self, **kwargs):
        app: Application = self.context["application"]
        for line in app.lines.select_related("vacancy"):
            line.line_salary_total = line.qty * line.vacancy.salary
            line.save(update_fields=["line_salary_total"])

        recalc_application_sum(app)
        apply_status_change(app, Application.Status.FORMED)
        return app


class ApplicationModerationSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=[("finish", "finish"), ("reject", "reject")])
    moderator_note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        app: Application = self.context["application"]
        if app.status != Application.Status.FORMED:
            raise serializers.ValidationError(
                {"status": "Модератор может обработать только сформированную заявку."}
            )
        return attrs

    def save(self, **kwargs):
        app: Application = self.context["application"]
        moderator = self.context.get("moderator")
        action = self.validated_data["action"]

        if "moderator_note" in self.validated_data:
            app.moderator_note = self.validated_data["moderator_note"]

        new_status = (
            Application.Status.FINISHED if action == "finish" else Application.Status.REJECTED
        )
        apply_status_change(app, new_status, moderator=moderator)
        app.save(update_fields=["moderator_note"])
        return app


class ApplicationDeleteSerializer(serializers.Serializer):
    def validate(self, attrs):
        app: Application = self.context["application"]
        if app.status != Application.Status.DRAFT:
            raise serializers.ValidationError(
                {"status": "Удалить можно только заявку в статусе черновика."}
            )
        return attrs

    def save(self, **kwargs):
        app: Application = self.context["application"]
        apply_status_change(app, Application.Status.DELETED)
        return app


class ApplicationLineMutationSerializer(serializers.Serializer):
    vacancy_id = serializers.IntegerField()
    qty = serializers.IntegerField(required=False, min_value=1)
    comment = serializers.CharField(required=False, allow_blank=True)
    is_main = serializers.BooleanField(required=False)
    order_index = serializers.IntegerField(required=False, min_value=1)

    def validate_vacancy_id(self, value):
        if not Vacancy.objects.filter(
            pk=value,
            is_active=True,
            moderation_status=Vacancy.ModerationStatus.APPROVED,
        ).exists():
            raise serializers.ValidationError("Активная вакансия не найдена.")
        return value


class VacancyModerationSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=[("approve", "approve"), ("reject", "reject")])
    moderation_note = serializers.CharField(required=False, allow_blank=True)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)
    role = serializers.ChoiceField(
        write_only=True,
        choices=[
            (UserAccount.Role.APPLICANT, "Соискатель"),
            (UserAccount.Role.EMPLOYER, "Работодатель"),
        ],
    )

    class Meta:
        model = User
        fields = ["id", "username", "password", "first_name", "last_name", "email", "role"]
        read_only_fields = ["id"]

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        role = validated_data.pop("role")

        user = User.objects.create_user(password=password, **validated_data)
        UserAccount.objects.create(user=user, role=role)

        if role == UserAccount.Role.APPLICANT:
            ApplicantProfile.objects.create(
                user=user,
                full_name=(f"{user.last_name} {user.first_name}".strip() or user.username),
                city="",
                phone="",
            )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserAccount.Role.choices)


class LoginResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    username = serializers.CharField()
    role = serializers.CharField()
    session_key = serializers.CharField(allow_null=True)


class LogoutResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class CurrentUserSerializer(serializers.Serializer):
    def to_representation(self, instance):
        request = self.context["request"]
        user = request.user
        return {
            "id": user.id,
            "username": user.username,
            "role": get_user_role(user),
            "full_name": user.get_full_name(),
            "email": user.email,
            "is_authenticated": user.is_authenticated,
            "session_key": request.session.session_key,
        }
