from django.contrib import admin

from .Models import ApplicantProfile, Application, ApplicationVacancy, UserAccount, Vacancy


@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email")


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "company",
        "city",
        "salary",
        "creator",
        "moderation_status",
        "moderator",
        "is_active",
    )
    list_filter = ("is_active", "moderation_status", "city")
    search_fields = ("title", "company", "city", "creator__username")


@admin.register(ApplicantProfile)
class ApplicantProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "full_name",
        "phone",
        "city",
        "age",
        "gender",
        "disability_category",
    )
    search_fields = ("full_name", "phone", "city", "user__username")


class ApplicationVacancyInline(admin.TabularInline):
    model = ApplicationVacancy
    extra = 0


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "creator",
        "applicant",
        "moderator",
        "created_at",
        "formed_at",
        "completed_at",
        "total_salary",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "id",
        "creator__username",
        "creator__first_name",
        "creator__last_name",
        "applicant__full_name",
        "applicant__phone",
    )
    inlines = (ApplicationVacancyInline,)


@admin.register(ApplicationVacancy)
class ApplicationVacancyAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "vacancy", "qty", "order_index", "is_main")
    list_filter = ("is_main",)
    search_fields = (
        "application__id",
        "vacancy__title",
        "vacancy__company",
    )
