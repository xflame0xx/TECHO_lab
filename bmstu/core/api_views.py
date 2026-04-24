from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .api_serializers import (
    ApplicationCartSerializer,
    ApplicationDeleteSerializer,
    ApplicationDetailSerializer,
    ApplicationFormSerializer,
    ApplicationLineMutationSerializer,
    ApplicationLineSerializer,
    ApplicationListSerializer,
    ApplicationModerationSerializer,
    ApplicationUpdateSerializer,
    CurrentUserSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    LogoutResponseSerializer,
    RegisterSerializer,
    VacancyModerationSerializer,
    VacancySerializer,
)
from .Models import Application, ApplicationVacancy, UserAccount, Vacancy
from .services import (
    approve_vacancy,
    ensure_demo_moderator,
    ensure_draft_application,
    get_application_list_queryset,
    get_public_vacancies_queryset,
    get_user_role,
    next_order_index,
    parse_date,
    recalc_application_sum,
    reject_vacancy,
)


class RoleAwareApiView(APIView):
    def require_authenticated(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Требуется авторизация."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return None

    def require_role(self, request, *roles):
        auth_error = self.require_authenticated(request)
        if auth_error:
            return auth_error
        if get_user_role(request.user) not in set(roles):
            return Response(
                {"detail": "Недостаточно прав."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None


@extend_schema_view(
    get=extend_schema(
        tags=["vacancies"],
        summary="Получить список опубликованных вакансий",
        description=(
            "Публичный метод. Без авторизации доступны только опубликованные вакансии. "
            "Поддерживает фильтрацию по search, company, city, schedule, disability_support."
        ),
        responses={200: VacancySerializer(many=True)},
        operation_id="vacancy_list",
    ),
    post=extend_schema(
        tags=["vacancies"],
        summary="Создать вакансию",
        description=(
            "Доступно только работодателю. Новая вакансия создаётся в статусе "
            "PENDING и отправляется на модерацию."
        ),
        request=VacancySerializer,
        responses={
            201: VacancySerializer,
            401: OpenApiResponse(description="Не авторизован"),
            403: OpenApiResponse(description="Недостаточно прав"),
        },
        operation_id="vacancy_create",
    ),
)
class VacancyListCreateApi(RoleAwareApiView):
    def get(self, request):
        search = request.query_params.get("search", "").strip()
        company = request.query_params.get("company", "").strip()
        city = request.query_params.get("city", "").strip()
        schedule = request.query_params.get("schedule", "").strip()
        disability_support = request.query_params.get("disability_support", "").strip()

        qs = get_public_vacancies_queryset()

        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(company__icontains=search)
                | Q(city__icontains=search)
            )
        if company:
            qs = qs.filter(company__icontains=company)
        if city:
            qs = qs.filter(city__icontains=city)
        if schedule:
            qs = qs.filter(schedule__icontains=schedule)
        if disability_support:
            qs = qs.filter(disability_support__icontains=disability_support)

        serializer = VacancySerializer(
            qs.order_by("id"),
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        role_error = self.require_role(request, UserAccount.Role.EMPLOYER)
        if role_error:
            return role_error

        serializer = VacancySerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        vacancy = serializer.save(
            creator=request.user,
            moderation_status=Vacancy.ModerationStatus.PENDING,
            is_active=False,
        )
        return Response(
            VacancySerializer(vacancy, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["vacancies"],
    summary="Получить вакансию",
    description="Публичный метод для опубликованной и одобренной вакансии.",
    responses={200: VacancySerializer},
    operation_id="vacancy_get",
)
class VacancyDetailApi(APIView):
    def get(self, request, pk):
        vacancy = get_object_or_404(
            Vacancy,
            pk=pk,
            is_active=True,
            moderation_status=Vacancy.ModerationStatus.APPROVED,
        )
        return Response(VacancySerializer(vacancy, context={"request": request}).data)


@extend_schema(
    tags=["vacancies"],
    summary="Промодерировать вакансию",
    description=(
        "Доступно только модератору. "
        "action=approve публикует вакансию, action=reject отклоняет её."
    ),
    request=VacancyModerationSerializer,
    responses={
        200: VacancySerializer,
        401: OpenApiResponse(description="Не авторизован"),
        403: OpenApiResponse(description="Недостаточно прав"),
    },
    operation_id="vacancy_moderate",
)
class VacancyModerationApi(RoleAwareApiView):
    def put(self, request, pk):
        role_error = self.require_role(request, UserAccount.Role.MODERATOR)
        if role_error:
            return role_error

        serializer = VacancyModerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vacancy = get_object_or_404(Vacancy, pk=pk)
        action = serializer.validated_data["action"]
        note = serializer.validated_data.get("moderation_note", "")

        if action == "approve":
            approve_vacancy(vacancy, request.user, note)
        else:
            reject_vacancy(vacancy, request.user, note)

        return Response(VacancySerializer(vacancy, context={"request": request}).data)


@extend_schema_view(
    post=extend_schema(
        tags=["applications"],
        summary="Добавить вакансию в черновик заявки",
        description=(
            "Добавляет вакансию в черновую заявку соискателя. "
            "Если черновика нет, он создаётся автоматически."
        ),
        request=ApplicationLineMutationSerializer,
        responses={201: OpenApiResponse(description="Вакансия добавлена в заявку")},
        operation_id="application_line_add",
    ),
    put=extend_schema(
        tags=["applications"],
        summary="Изменить строку заявки",
        description=(
            "Обновляет количество, комментарий, признак основной позиции "
            "и порядок строки в черновике заявки."
        ),
        request=ApplicationLineMutationSerializer,
        responses={200: ApplicationLineSerializer},
        operation_id="application_line_update",
    ),
    delete=extend_schema(
        tags=["applications"],
        summary="Удалить вакансию из черновика заявки",
        description="Удаляет выбранную вакансию из черновой заявки соискателя.",
        request=ApplicationLineMutationSerializer,
        responses={204: OpenApiResponse(description="Строка удалена")},
        operation_id="application_line_delete",
    ),
)
class ApplicationLineApi(RoleAwareApiView):
    def post(self, request):
        role_error = self.require_role(request, UserAccount.Role.APPLICANT)
        if role_error:
            return role_error

        serializer = ApplicationLineMutationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        app = ensure_draft_application(request.user)
        vacancy = get_object_or_404(
            Vacancy,
            pk=serializer.validated_data["vacancy_id"],
            is_active=True,
            moderation_status=Vacancy.ModerationStatus.APPROVED,
        )

        line = app.lines.filter(vacancy=vacancy).first()
        if line is None:
            line = ApplicationVacancy.objects.create(
                application=app,
                vacancy=vacancy,
                qty=serializer.validated_data.get("qty", 1),
                comment=serializer.validated_data.get("comment", ""),
                is_main=serializer.validated_data.get("is_main", False),
                order_index=serializer.validated_data.get(
                    "order_index",
                    next_order_index(app),
                ),
            )
        else:
            if "qty" in serializer.validated_data:
                line.qty = serializer.validated_data["qty"]
            if "comment" in serializer.validated_data:
                line.comment = serializer.validated_data["comment"]
            if "is_main" in serializer.validated_data:
                line.is_main = serializer.validated_data["is_main"]
            if "order_index" in serializer.validated_data:
                line.order_index = serializer.validated_data["order_index"]
            line.save()

        recalc_application_sum(app)
        line.refresh_from_db()

        return Response(
            {
                "application_id": app.id,
                "line": ApplicationLineSerializer(
                    line,
                    context={"request": request},
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def put(self, request):
        role_error = self.require_role(request, UserAccount.Role.APPLICANT)
        if role_error:
            return role_error

        serializer = ApplicationLineMutationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        app = get_object_or_404(
            Application,
            creator=request.user,
            status=Application.Status.DRAFT,
        )
        line = get_object_or_404(
            ApplicationVacancy,
            application=app,
            vacancy_id=serializer.validated_data["vacancy_id"],
        )

        for field in ["qty", "comment", "is_main", "order_index"]:
            if field in serializer.validated_data:
                setattr(line, field, serializer.validated_data[field])

        line.save()
        recalc_application_sum(app)
        line.refresh_from_db()
        return Response(ApplicationLineSerializer(line, context={"request": request}).data)

    def delete(self, request):
        role_error = self.require_role(request, UserAccount.Role.APPLICANT)
        if role_error:
            return role_error

        serializer = ApplicationLineMutationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        app = get_object_or_404(
            Application,
            creator=request.user,
            status=Application.Status.DRAFT,
        )
        line = get_object_or_404(
            ApplicationVacancy,
            application=app,
            vacancy_id=serializer.validated_data["vacancy_id"],
        )
        line.delete()
        recalc_application_sum(app)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["applications"],
    summary="Получить состояние корзины заявки",
    description="Возвращает id черновой заявки и количество вакансий в ней.",
    responses={200: ApplicationCartSerializer},
    operation_id="application_cart_get",
)
class ApplicationCartApi(RoleAwareApiView):
    def get(self, request):
        role_error = self.require_role(request, UserAccount.Role.APPLICANT)
        if role_error:
            return role_error

        app = Application.objects.filter(
            creator=request.user,
            status=Application.Status.DRAFT,
        ).first()

        payload = {
            "application_id": app.id if app else None,
            "items_count": app.lines.count() if app else 0,
        }
        return Response(ApplicationCartSerializer(payload).data)


@extend_schema_view(
    get=extend_schema(
        tags=["applications"],
        summary="Получить список заявок",
        description=(
            "Соискатель видит только свои заявки. "
            "Модератор видит все заявки. "
            "Гость получает 401."
        ),
        responses={
            200: ApplicationListSerializer(many=True),
            401: OpenApiResponse(description="Требуется авторизация"),
            403: OpenApiResponse(description="Недостаточно прав"),
        },
        operation_id="application_list",
    )
)
class ApplicationListApi(RoleAwareApiView):
    def get(self, request):
        role_error = self.require_role(
            request,
            UserAccount.Role.APPLICANT,
            UserAccount.Role.MODERATOR,
        )
        if role_error:
            return role_error

        status_value = request.query_params.get("status", "").strip()
        date_from = parse_date(request.query_params.get("date_from", ""))
        date_to = parse_date(request.query_params.get("date_to", ""))

        qs = get_application_list_queryset(request.user)

        if status_value:
            qs = qs.filter(status=status_value)
        if date_from:
            qs = qs.filter(formed_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(formed_at__date__lte=date_to)

        return Response(ApplicationListSerializer(qs, many=True).data)


@extend_schema_view(
    get=extend_schema(
        tags=["applications"],
        summary="Получить заявку",
        description=(
            "Соискатель может получить только свою заявку. " "Модератор может открыть любую заявку."
        ),
        responses={200: ApplicationDetailSerializer},
        operation_id="application_get",
    ),
    put=extend_schema(
        tags=["applications"],
        summary="Обновить черновик заявки",
        description=(
            "Обновляет данные заявителя, контактную информацию "
            "и сопроводительное письмо в заявке соискателя."
        ),
        request=ApplicationUpdateSerializer,
        responses={200: ApplicationDetailSerializer},
        operation_id="application_update",
    ),
)
class ApplicationDetailUpdateApi(RoleAwareApiView):
    def get_object(self, request, pk):
        qs = Application.objects.select_related(
            "creator", "moderator", "applicant"
        ).prefetch_related("lines__vacancy")

        if get_user_role(request.user) == UserAccount.Role.MODERATOR:
            return get_object_or_404(qs, pk=pk)
        return get_object_or_404(qs, pk=pk, creator=request.user)

    def get(self, request, pk):
        role_error = self.require_role(
            request,
            UserAccount.Role.APPLICANT,
            UserAccount.Role.MODERATOR,
        )
        if role_error:
            return role_error

        app = self.get_object(request, pk)
        if app.status == Application.Status.DELETED:
            return Response(
                {"detail": "Заявка удалена."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ApplicationDetailSerializer(app, context={"request": request}).data)

    def put(self, request, pk):
        role_error = self.require_role(request, UserAccount.Role.APPLICANT)
        if role_error:
            return role_error

        app = get_object_or_404(Application, pk=pk, creator=request.user)
        serializer = ApplicationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(app, serializer.validated_data)
        return Response(ApplicationDetailSerializer(app, context={"request": request}).data)


@extend_schema(
    tags=["applications"],
    summary="Сформировать заявку",
    description=(
        "Переводит заявку из статуса DRAFT в FORMED. "
        "Перед формированием проверяется заполненность профиля и наличие "
        "хотя бы одной вакансии в заявке."
    ),
    responses={200: ApplicationDetailSerializer},
    operation_id="application_form",
)
class ApplicationFormApi(RoleAwareApiView):
    def put(self, request, pk):
        role_error = self.require_role(request, UserAccount.Role.APPLICANT)
        if role_error:
            return role_error

        app = get_object_or_404(Application, pk=pk, creator=request.user)
        serializer = ApplicationFormSerializer(
            data=request.data or {},
            context={"application": app},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ApplicationDetailSerializer(app, context={"request": request}).data)


@extend_schema(
    tags=["applications"],
    summary="Завершить или отклонить заявку модератором",
    description=("Только модератор может выполнять этот метод. " "Создатель заявки получит 403."),
    request=ApplicationModerationSerializer,
    responses={
        200: ApplicationDetailSerializer,
        401: OpenApiResponse(description="Требуется авторизация"),
        403: OpenApiResponse(description="Недостаточно прав"),
    },
    operation_id="application_moderate",
)
class ApplicationModerationApi(RoleAwareApiView):
    def put(self, request, pk):
        role_error = self.require_role(request, UserAccount.Role.MODERATOR)
        if role_error:
            return role_error

        app = get_object_or_404(Application, pk=pk)
        serializer = ApplicationModerationSerializer(
            data=request.data,
            context={"application": app, "moderator": request.user},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ApplicationDetailSerializer(app, context={"request": request}).data)


@extend_schema(
    tags=["applications"],
    summary="Удалить заявку",
    description="Удаляет заявку соискателя, если она находится в статусе черновика.",
    responses={204: OpenApiResponse(description="Заявка удалена")},
    operation_id="application_delete",
)
class ApplicationDeleteApi(RoleAwareApiView):
    def delete(self, request, pk):
        role_error = self.require_role(request, UserAccount.Role.APPLICANT)
        if role_error:
            return role_error

        app = get_object_or_404(Application, pk=pk, creator=request.user)
        serializer = ApplicationDeleteSerializer(data={}, context={"application": app})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["auth"],
    summary="Регистрация",
    description=(
        "Создание аккаунта работодателя или соискателя. "
        "После регистрации пользователь автоматически авторизуется через сессию."
    ),
    request=RegisterSerializer,
    responses={201: OpenApiResponse(description="Пользователь создан")},
    operation_id="auth_register",
)
class RegisterApi(APIView):
    def post(self, request):
        ensure_demo_moderator()
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "role": get_user_role(user),
                "session_key": request.session.session_key,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["auth"],
    summary="Вход",
    description=(
        "Авторизация через Django session + cookie. "
        "После успешного входа в браузере появится cookie sessionid. "
        "В Swagger дальнейшие запросы можно выполнять в том же окне браузера."
    ),
    request=LoginSerializer,
    responses={200: LoginResponseSerializer},
    examples=[
        OpenApiExample(
            "Вход соискателя",
            value={"username": "applicant1", "password": "1234", "role": "applicant"},
            request_only=True,
        ),
        OpenApiExample(
            "Вход работодателя",
            value={"username": "employer1", "password": "1234", "role": "employer"},
            request_only=True,
        ),
        OpenApiExample(
            "Вход модератора",
            value={
                "username": "Ilya Snytkin",
                "password": "Ilya123",
                "role": "moderator",
            },
            request_only=True,
        ),
    ],
    operation_id="auth_login",
)
class LoginApi(APIView):
    def post(self, request):
        ensure_demo_moderator()
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        selected_role = serializer.validated_data["role"]

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Неверный логин или пароль."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        actual_role = get_user_role(user)
        if selected_role != actual_role:
            return Response(
                {"detail": "Выбранная роль не соответствует аккаунту."},
                status=status.HTTP_403_FORBIDDEN,
            )

        login(request, user)

        return Response(
            {
                "message": "Авторизация выполнена успешно.",
                "username": user.username,
                "role": actual_role,
                "session_key": request.session.session_key,
            }
        )


@extend_schema(
    tags=["auth"],
    summary="Выход",
    description="Удаляет текущую сессию пользователя.",
    responses={200: LogoutResponseSerializer},
    operation_id="auth_logout",
)
class LogoutApi(RoleAwareApiView):
    def post(self, request):
        auth_error = self.require_authenticated(request)
        if auth_error:
            return auth_error
        logout(request)
        return Response({"message": "Вы вышли из системы."})


@extend_schema(
    tags=["auth"],
    summary="Текущий пользователь",
    description="Возвращает текущего авторизованного пользователя и его роль.",
    responses={200: CurrentUserSerializer},
    operation_id="auth_me",
)
class CurrentUserApi(RoleAwareApiView):
    def get(self, request):
        auth_error = self.require_authenticated(request)
        if auth_error:
            return auth_error
        return Response(
            CurrentUserSerializer(
                instance=request.user,
                context={"request": request},
            ).data
        )
