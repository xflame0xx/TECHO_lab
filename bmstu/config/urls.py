"""URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from core import api_views, views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home_redirect, name="home"),
    path("vacancies/", views.vacancies_list, name="vacancies"),
    path("vacancies/<int:id>/", views.vacancy_detail, name="vacancy"),
    path("applications/", views.applications_list, name="applications"),
    path("applications/<int:id>/", views.application_detail, name="application"),
    path("applications/add/<int:id>/", views.add_to_application, name="add_to_application"),
    path("applications/delete/<int:id>/", views.delete_application, name="delete_application"),
    path("api/vacancies/", api_views.VacancyListCreateApi.as_view(), name="api-vacancies"),
    path("api/vacancies/<int:pk>/", api_views.VacancyDetailApi.as_view(), name="api-vacancy"),
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
    path("api/users/login/", api_views.LoginStubApi.as_view(), name="api-users-login"),
    path("api/users/logout/", api_views.LogoutStubApi.as_view(), name="api-users-logout"),
]

if not settings.USE_MINIO:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
