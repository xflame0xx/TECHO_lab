from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core import api_views, views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home_redirect, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_redirect, name="dashboard"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("vacancies/", views.vacancies_list, name="vacancies"),
    path("vacancies/<int:id>/", views.vacancy_detail, name="vacancy"),
    path("applications/", views.applications_list, name="applications"),
    path("applications/<int:id>/", views.application_detail, name="application"),
    path("applications/add/<int:id>/", views.add_to_application, name="add_to_application"),
    path("applications/delete/<int:id>/", views.delete_application, name="delete_application"),
    path("cabinet/applicant/", views.applicant_cabinet, name="applicant_cabinet"),
    path("cabinet/employer/", views.employer_cabinet, name="employer_cabinet"),
    path("cabinet/employer/responses/", views.employer_responses, name="employer_responses"),
    path("cabinet/moderator/", views.moderator_cabinet, name="moderator_cabinet"),
    path("api/vacancies/", api_views.VacancyListCreateApi.as_view(), name="api-vacancies"),
    path("api/vacancies/<int:pk>/", api_views.VacancyDetailApi.as_view(), name="api-vacancy"),
    path(
        "api/vacancies/<int:pk>/moderate/",
        api_views.VacancyModerationApi.as_view(),
        name="api-vacancy-moderate",
    ),
    path(
        "api/application-lines/",
        api_views.ApplicationLineApi.as_view(),
        name="api-application-lines",
    ),
    path(
        "api/applications/cart/",
        api_views.ApplicationCartApi.as_view(),
        name="api-applications-cart",
    ),
    path("api/applications/", api_views.ApplicationListApi.as_view(), name="api-applications"),
    path(
        "api/applications/<int:pk>/",
        api_views.ApplicationDetailUpdateApi.as_view(),
        name="api-application",
    ),
    path(
        "api/applications/<int:pk>/form/",
        api_views.ApplicationFormApi.as_view(),
        name="api-application-form",
    ),
    path(
        "api/applications/<int:pk>/moderate/",
        api_views.ApplicationModerationApi.as_view(),
        name="api-application-moderate",
    ),
    path(
        "api/applications/<int:pk>/delete/",
        api_views.ApplicationDeleteApi.as_view(),
        name="api-application-delete",
    ),
    path("api/users/register/", api_views.RegisterApi.as_view(), name="api-users-register"),
    path("api/users/login/", api_views.LoginApi.as_view(), name="api-users-login"),
    path("api/users/logout/", api_views.LogoutApi.as_view(), name="api-users-logout"),
    path("api/users/me/", api_views.CurrentUserApi.as_view(), name="api-users-me"),
]

if not settings.USE_MINIO:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
