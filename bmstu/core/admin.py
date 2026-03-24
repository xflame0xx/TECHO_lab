from django.contrib import admin

from .Models import ApplicantProfile, Application, ApplicationVacancy, Vacancy


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "company", "city", "salary", "is_active")
    list_filter = ("is_active", "city")
    search_fields = ("title", "company", "city")


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
        "created_at",
        "formed_at_display",
        "finished_at_display",
        "result_sum_display",
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

    @admin.display(description="Дата формирования")
    def formed_at_display(self, obj):
        return getattr(obj, "formed_at", None) or "—"

    @admin.display(description="Дата завершения")
    def finished_at_display(self, obj):
        for name in ("finished_at", "completed_at", "closed_at"):
            val = getattr(obj, name, None)
            if val:
                return val
        return "—"

    @admin.display(description="Результат (сумма)")
    def result_sum_display(self, obj):
        for name in ("result_sum", "total_salary", "total_sum", "total"):
            if hasattr(obj, name):
                val = getattr(obj, name)
                if val is not None:
                    return val
        return "—"


@admin.register(ApplicationVacancy)
class ApplicationVacancyAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "vacancy", "qty", "position_display", "is_main")
    list_filter = ("is_main",)
    search_fields = (
        "application__id",
        "vacancy__title",
        "vacancy__company",
    )

    @admin.display(description="Порядок")
    def position_display(self, obj):
        for name in ("order_index", "position", "order", "sort", "sort_order"):
            if hasattr(obj, name):
                return getattr(obj, name)
        return "—"
