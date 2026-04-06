from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from core.Models import Vacancy


@override_settings(DJANGO_USE_MINIO=False)
class Lab3ApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.vacancy1 = Vacancy.objects.create(
            title="Python разработчик",
            company="Техно",
            city="Москва",
            salary=120000,
            description="Backend",
            disability_support="Да",
            schedule="Удаленно",
        )
        self.vacancy2 = Vacancy.objects.create(
            title="QA инженер",
            company="Техно",
            city="Казань",
            salary=90000,
            description="Testing",
            disability_support="Частично",
            schedule="Гибрид",
        )

    def test_full_application_flow(self):
        response = self.client.post(
            "/api/application-lines/", {"vacancy_id": self.vacancy1.id}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        app_id = response.json()["application_id"]

        response = self.client.post(
            "/api/application-lines/", {"vacancy_id": self.vacancy2.id}, format="json"
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.put(
            f"/api/applications/{app_id}/",
            {
                "full_name": "Иванов Иван",
                "phone": "+79990000000",
                "city": "Москва",
                "contact_email": "ivanov@example.com",
                "cover_letter": "Хочу работать",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.put(f"/api/applications/{app_id}/form/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "FORMED")

        response = self.client.put(
            f"/api/applications/{app_id}/moderate/",
            {"action": "finish", "moderator_note": "ok"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "FINISHED")

    def test_cannot_moderate_draft(self):
        response = self.client.post(
            "/api/application-lines/", {"vacancy_id": self.vacancy1.id}, format="json"
        )
        app_id = response.json()["application_id"]

        response = self.client.put(
            f"/api/applications/{app_id}/moderate/",
            {"action": "finish"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_vacancy_filter(self):
        response = self.client.get("/api/vacancies/?search=Python&city=Москва")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.vacancy1.id)

    def test_register_user(self):
        response = self.client.post(
            "/api/users/register/",
            {
                "username": "new_user",
                "password": "1234",
                "first_name": "New",
                "last_name": "User",
                "email": "new@example.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
