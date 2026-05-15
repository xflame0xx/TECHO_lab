const BACKEND_URL = "http://127.0.0.1:9003";

export const ROUTES = {
  HOME: "/",

  LOGIN: "/login",
  REGISTER: "/register",

  VACANCIES: "/vacancies",
  VACANCY_DETAIL: "/vacancies/:id",

  APPLICATIONS: "/applications",
  APPLICATION_DETAIL: "/applications/:id",

  APPLICANT_CABINET: "/cabinet/applicant",
  EMPLOYER_CABINET: "/cabinet/employer",
  EMPLOYER_RESPONSES: "/cabinet/employer/responses",
  MODERATOR_CABINET: "/cabinet/moderator",

  SWAGGER: `${BACKEND_URL}/swagger/`,
  ADMIN: `${BACKEND_URL}/admin/`,
};

export const ROUTE_LABELS = {
  HOME: "Главная",

  LOGIN: "Вход",
  REGISTER: "Регистрация",

  VACANCIES: "Вакансии",
  VACANCY_DETAIL: "Вакансия",

  APPLICATIONS: "Заявки",
  APPLICATION_DETAIL: "Заявка",

  APPLICANT_CABINET: "Кабинет соискателя",
  EMPLOYER_CABINET: "Кабинет работодателя",
  EMPLOYER_RESPONSES: "Отклики",
  MODERATOR_CABINET: "Кабинет модератора",
};
