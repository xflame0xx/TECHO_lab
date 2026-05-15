import { MOCK_VACANCIES } from "./mockVacancies";
import type { ApplicationDetail, ApplicationListItem } from "../types/application";

export const MOCK_APPLICATIONS: ApplicationDetail[] = [
  {
    id: 1,
    status: "DRAFT",
    creator_login: "applicant",
    moderator_login: null,
    created_at: "2026-04-21T10:00:00Z",
    formed_at: null,
    completed_at: null,
    contact_email: "applicant@example.com",
    cover_letter:
      "Хочу рассмотреть вакансии с гибким графиком и возможностью удалённой работы.",
    estimated_response_date: null,
    moderator_note: "",
    total_salary: 320000,
    applicant: {
      id: 1,
      full_name: "Иванов Иван Иванович",
      phone: "+7 (900) 000-00-00",
      city: "Москва",
      age: 22,
      gender: "male",
      disability_category: "none",
    },
    lines: [
      {
        id: 1,
        vacancy: MOCK_VACANCIES[0],
        qty: 1,
        comment: "Интересует React и удалённая работа.",
        is_main: true,
        order_index: 1,
        line_salary_total: 150000,
        calculated_result: 150000,
      },
      {
        id: 2,
        vacancy: MOCK_VACANCIES[1],
        qty: 1,
        comment: "Подходит backend-направление.",
        is_main: false,
        order_index: 2,
        line_salary_total: 170000,
        calculated_result: 170000,
      },
    ],
  },
  {
    id: 2,
    status: "FORMED",
    creator_login: "applicant",
    moderator_login: null,
    created_at: "2026-04-15T12:00:00Z",
    formed_at: "2026-04-16T09:30:00Z",
    completed_at: null,
    contact_email: "applicant@example.com",
    cover_letter: "Прошу рассмотреть мою заявку.",
    estimated_response_date: "2026-04-25",
    moderator_note: "",
    total_salary: 90000,
    applicant: {
      id: 1,
      full_name: "Иванов Иван Иванович",
      phone: "+7 (900) 000-00-00",
      city: "Москва",
      age: 22,
      gender: "male",
      disability_category: "none",
    },
    lines: [
      {
        id: 3,
        vacancy: MOCK_VACANCIES[2],
        qty: 1,
        comment: "Есть опыт ручного тестирования.",
        is_main: true,
        order_index: 1,
        line_salary_total: 90000,
        calculated_result: 90000,
      },
    ],
  },
];

export const toApplicationListItem = (
  application: ApplicationDetail,
): ApplicationListItem => {
  const totalSum = application.lines.reduce(
    (sum, line) => sum + (line.line_salary_total ?? line.qty * line.vacancy.salary),
    0,
  );

  return {
    id: application.id,
    status: application.status,
    creator_login: application.creator_login,
    moderator_login: application.moderator_login,
    applicant_name: application.applicant?.full_name || null,
    created_at: application.created_at,
    formed_at: application.formed_at,
    completed_at: application.completed_at,
    contact_email: application.contact_email,
    estimated_response_date: application.estimated_response_date,
    total_salary: totalSum,
    lines_count: application.lines.length,
    calculated_lines_count: application.lines.length,
    total_sum: totalSum,
  };
};
