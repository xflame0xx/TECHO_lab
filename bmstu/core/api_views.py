from django.db.models import Q
from django.shortcuts import get_object_or_404
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
    RegisterSerializer,
    VacancySerializer,
)
from .Models import Application, ApplicationVacancy, Vacancy
from .services import (
    ensure_draft_application,
    get_application_list_queryset,
    get_constant_creator,
    next_order_index,
    parse_date,
    recalc_application_sum,
)


class VacancyListCreateApi(APIView):
    def get(self, request):
        search = request.query_params.get("search", "").strip()
        company = request.query_params.get("company", "").strip()
        city = request.query_params.get("city", "").strip()
        schedule = request.query_params.get("schedule", "").strip()
        disability_support = request.query_params.get("disability_support", "").strip()

        qs = Vacancy.objects.filter(is_active=True)

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

        serializer = VacancySerializer(qs.order_by("id"), many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        serializer = VacancySerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        vacancy = serializer.save()
        return Response(
            VacancySerializer(vacancy, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class VacancyDetailApi(APIView):
    def get(self, request, pk):
        vacancy = get_object_or_404(Vacancy, pk=pk, is_active=True)
        return Response(VacancySerializer(vacancy, context={"request": request}).data)


class ApplicationLineApi(APIView):
    def post(self, request):
        creator = get_constant_creator()
        serializer = ApplicationLineMutationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        app = ensure_draft_application(creator)
        vacancy = get_object_or_404(
            Vacancy, pk=serializer.validated_data["vacancy_id"], is_active=True
        )

        line = app.lines.filter(vacancy=vacancy).first()
        if line is None:
            line = ApplicationVacancy.objects.create(
                application=app,
                vacancy=vacancy,
                qty=serializer.validated_data.get("qty", 1),
                comment=serializer.validated_data.get("comment", ""),
                is_main=serializer.validated_data.get("is_main", False),
                order_index=serializer.validated_data.get("order_index", next_order_index(app)),
            )
        else:
            if "qty" in serializer.validated_data:
                line.qty = serializer.validated_data["qty"]
            line.save()

        recalc_application_sum(app)
        line.refresh_from_db()
        return Response(
            {
                "application_id": app.id,
                "line": ApplicationLineSerializer(line, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def put(self, request):
        creator = get_constant_creator()
        serializer = ApplicationLineMutationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        app = get_object_or_404(Application, creator=creator, status=Application.Status.DRAFT)
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
        creator = get_constant_creator()
        serializer = ApplicationLineMutationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        app = get_object_or_404(Application, creator=creator, status=Application.Status.DRAFT)
        line = get_object_or_404(
            ApplicationVacancy,
            application=app,
            vacancy_id=serializer.validated_data["vacancy_id"],
        )
        line.delete()
        recalc_application_sum(app)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApplicationCartApi(APIView):
    def get(self, request):
        creator = get_constant_creator()
        app = Application.objects.filter(creator=creator, status=Application.Status.DRAFT).first()
        payload = {
            "application_id": app.id if app else None,
            "items_count": app.lines.count() if app else 0,
        }
        return Response(ApplicationCartSerializer(payload).data)


class ApplicationListApi(APIView):
    def get(self, request):
        creator = get_constant_creator()
        status_value = request.query_params.get("status", "").strip()
        date_from = parse_date(request.query_params.get("date_from", ""))
        date_to = parse_date(request.query_params.get("date_to", ""))

        qs = get_application_list_queryset(creator)

        if status_value:
            qs = qs.filter(status=status_value)
        if date_from:
            qs = qs.filter(formed_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(formed_at__date__lte=date_to)

        return Response(ApplicationListSerializer(qs, many=True).data)


class ApplicationDetailUpdateApi(APIView):
    def get_object(self, pk):
        creator = get_constant_creator()
        return get_object_or_404(
            Application.objects.select_related(
                "creator", "moderator", "applicant"
            ).prefetch_related("lines__vacancy"),
            pk=pk,
            creator=creator,
        )

    def get(self, request, pk):
        app = self.get_object(pk)
        if app.status == Application.Status.DELETED:
            return Response({"detail": "Заявка удалена."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ApplicationDetailSerializer(app, context={"request": request}).data)

    def put(self, request, pk):
        app = self.get_object(pk)
        serializer = ApplicationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(app, serializer.validated_data)
        return Response(ApplicationDetailSerializer(app, context={"request": request}).data)


class ApplicationFormApi(APIView):
    def put(self, request, pk):
        creator = get_constant_creator()
        app = get_object_or_404(Application, pk=pk, creator=creator)
        serializer = ApplicationFormSerializer(
            data=request.data or {}, context={"application": app}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ApplicationDetailSerializer(app, context={"request": request}).data)


class ApplicationModerationApi(APIView):
    def put(self, request, pk):
        creator = get_constant_creator()
        app = get_object_or_404(Application, pk=pk, creator=creator)
        serializer = ApplicationModerationSerializer(
            data=request.data, context={"application": app}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ApplicationDetailSerializer(app, context={"request": request}).data)


class ApplicationDeleteApi(APIView):
    def delete(self, request, pk):
        creator = get_constant_creator()
        app = get_object_or_404(Application, pk=pk, creator=creator)
        serializer = ApplicationDeleteSerializer(data={}, context={"application": app})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegisterApi(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(RegisterSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginStubApi(APIView):
    def post(self, request):
        return Response(
            {
                "message": "Заглушка авторизации для лабораторной 4.",
                "creator_user": "creator_demo",
                "moderator_user": "moderator_demo",
            }
        )


class LogoutStubApi(APIView):
    def post(self, request):
        return Response({"message": "Заглушка деавторизации для лабораторной 4."})
