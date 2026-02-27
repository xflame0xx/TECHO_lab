from django.shortcuts import render

# Услуги = вакансии (без БД)
vacancies = [
    {
        "id": 1,
        "title": "Оператор call-центра (удалённо)",
        "salary": 55000,
        "city": "Москва",
        "schedule": "5/2, 8 часов",
        "published": "2024-03-12",
        "employer": "Контакт-Сервис",
        "description": """Вакансия для соискателей с инвалидностью. Работа из дома.
Обязанности: приём входящих звонков, консультации, оформление обращений в системе.
Требования: грамотная речь, базовые навыки ПК, стабильный интернет.
Условия: обучение, поддержка наставника, официальное оформление.""",
        "image": "callcenter.png",
        "video": "callcenter_intro.mp4",
    },
    {
        "id": 2,
        "title": "Контент-менеджер (частичная занятость)",
        "salary": 45000,
        "city": "Санкт-Петербург",
        "schedule": "Гибкий график",
        "published": "2024-02-10",
        "employer": "MediaGroup",
        "description": """Вакансия адаптирована для соискателей с инвалидностью.
Обязанности: размещение материалов на сайте, базовая работа с изображениями, проверка текстов.
Требования: внимательность, навыки работы с браузером и офисными сервисами.
Условия: частичная занятость, понятные задачи, удалённый формат возможен.""",
        "image": "content.png",
        "video": "content_intro.mp4",
    },
    {
        "id": 3,
        "title": "Специалист по документообороту",
        "salary": 60000,
        "city": "Казань",
        "schedule": "5/2",
        "published": "2024-01-05",
        "employer": "Партнёр-Логистика",
        "description": """Вакансия для трудоустройства людей с инвалидностью.
Обязанности: подготовка и проверка документов, ведение реестров, работа с первичкой.
Требования: аккуратность, ответственность, базовый Excel.
Условия: офис/гибрид, доступная среда (обсуждается), официальное оформление.""",
        "image": "docs.png",
        "video": "docs_intro.mp4",
    },
]

# Заявка
application = {
    "id": 101,
    "candidate_name": "Иванов Иван Иванович",
    "disability": "Инвалидность II группы",
    "contact": "+7 (999) 111-22-33",
    "result": "Предварительная оценка: 2 заявки отправлены",
    # vacancy_id -> meta
    "items": {
        1: {"qty": 1, "mm": "Готов к обучению, есть опыт общения с клиентами"},
        3: {"qty": 1, "mm": "Опыт работы с документами, хочу гибрид"},
    },
}


def VacanciesList(request):
    """Список вакансий + поиск."""
    search = request.GET.get("search", "")
    result = vacancies

    if search:
        tmp = []
        for v in vacancies:
            if search.lower() in v["title"].lower():
                tmp.append(v)
            elif search.lower() in v["city"].lower():
                tmp.append(v)
            elif search in str(v["salary"]):
                tmp.append(v)
            elif search in v["published"]:
                tmp.append(v)
        result = tmp

    cart_count = 0
    for meta in application["items"].values():
        cart_count += meta.get("qty", 0)

    return render(
        request,
        "vacancies.html",
        {
            "vacancies": result,
            "application": application,
            "cart_count": cart_count,
            "search": search,
        },
    )


def VacancyDetail(request, id):
    """ренде детальной вакансии."""
    vacancy = None
    for v in vacancies:
        if v["id"] == id:
            vacancy = v
            break

    return render(request, "vacancy.html", {"vacancy": vacancy})


def ApplicationDetail(request, id):
    """рендер заявки(для примера)."""
    items = []
    total_qty = 0

    for vacancy_id, meta in application["items"].items():
        vacancy = None
        for v in vacancies:
            if v["id"] == vacancy_id:
                vacancy = v
                break

        if vacancy:
            qty = meta.get("qty", 0)
            total_qty += qty

            items.append({"vacancy": vacancy, "qty": qty, "mm": meta.get("mm", "")})

    return render(
        request,
        "application.html",
        {"application": application, "items": items, "total_qty": total_qty},
    )
