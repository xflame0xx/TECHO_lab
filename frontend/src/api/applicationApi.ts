import { apiRequest, isMockMode } from "./apiClient";
import { MOCK_APPLICATIONS, toApplicationListItem } from "../data/mockApplications";
import type {
  AddVacancyToApplicationResponse,
  ApplicationCart,
  ApplicationDetail,
  ApplicationFilters,
  ApplicationLine,
  ApplicationLineUpdatePayload,
  ApplicationListItem,
  ApplicationModerationPayload,
  ApplicationUpdatePayload,
} from "../types/application";

let mockApplications: ApplicationDetail[] = structuredClone(MOCK_APPLICATIONS);

const delay = (ms: number) => {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
};

const recalcMockApplication = (application: ApplicationDetail): ApplicationDetail => {
  const total = application.lines.reduce(
    (sum, line) => sum + line.qty * line.vacancy.salary,
    0,
  );

  return {
    ...application,
    total_salary: total,
    lines: application.lines.map((line) => ({
      ...line,
      line_salary_total: line.qty * line.vacancy.salary,
      calculated_result: line.qty * line.vacancy.salary,
    })),
  };
};

const findMockDraft = (): ApplicationDetail | undefined => {
  return mockApplications.find((application) => application.status === "DRAFT");
};

const isDateInRange = (
  dateValue: string | null,
  dateFrom: string,
  dateTo: string,
): boolean => {
  if (!dateFrom && !dateTo) {
    return true;
  }

  if (!dateValue) {
    return false;
  }

  const date = new Date(dateValue);
  const from = dateFrom ? new Date(`${dateFrom}T00:00:00`) : null;
  const to = dateTo ? new Date(`${dateTo}T23:59:59`) : null;

  if (from && date < from) {
    return false;
  }

  if (to && date > to) {
    return false;
  }

  return true;
};

export const fetchApplicationCart = async (): Promise<ApplicationCart | null> => {
  if (isMockMode()) {
    await delay(150);

    const draft = findMockDraft();

    return {
      application_id: draft?.id ?? null,
      items_count: draft?.lines.length ?? 0,
    };
  }

  try {
    return await apiRequest<ApplicationCart>("/api/applications/cart/");
  } catch {
    return null;
  }
};

export const addVacancyToApplication = async (
  vacancyId: number,
): Promise<AddVacancyToApplicationResponse> => {
  if (isMockMode()) {
    await delay(200);

    const draft = findMockDraft();

    if (!draft) {
      throw new Error("Черновая заявка не найдена в mock-данных");
    }

    const existingLine = draft.lines.find((line) => line.vacancy.id === vacancyId);

    if (existingLine) {
      existingLine.qty += 1;
      existingLine.line_salary_total = existingLine.qty * existingLine.vacancy.salary;
      existingLine.calculated_result = existingLine.line_salary_total;

      return {
        application_id: draft.id,
        line: existingLine,
      };
    }

    throw new Error("В mock-режиме добавлять можно только заранее подготовленные вакансии");
  }

  return apiRequest<AddVacancyToApplicationResponse>("/api/application-lines/", {
    method: "POST",
    json: {
      vacancy_id: vacancyId,
      qty: 1,
    },
  });
};

export const fetchApplications = async (
  filters: ApplicationFilters,
): Promise<ApplicationListItem[]> => {
  if (isMockMode()) {
    await delay(250);

    return mockApplications
      .map(toApplicationListItem)
      .filter((application) => {
        const matchesStatus =
          !filters.status || application.status === filters.status;

        const dateForFilter = application.formed_at || application.created_at;

        const matchesDate = isDateInRange(
          dateForFilter,
          filters.dateFrom,
          filters.dateTo,
        );

        return matchesStatus && matchesDate;
      });
  }

  const params = new URLSearchParams();

  if (filters.status) {
    params.set("status", filters.status);
  }

  if (filters.dateFrom) {
    params.set("date_from", filters.dateFrom);
  }

  if (filters.dateTo) {
    params.set("date_to", filters.dateTo);
  }

  const url = params.toString()
    ? `/api/applications/?${params.toString()}`
    : "/api/applications/";

  return apiRequest<ApplicationListItem[]>(url);
};

export const fetchApplicationById = async (
  id: string,
): Promise<ApplicationDetail> => {
  if (isMockMode()) {
    await delay(250);

    const application = mockApplications.find((item) => String(item.id) === id);

    if (!application) {
      throw new Error("Заявка не найдена");
    }

    return structuredClone(application);
  }

  return apiRequest<ApplicationDetail>(`/api/applications/${id}/`);
};

export const updateApplication = async (
  id: number,
  payload: ApplicationUpdatePayload,
): Promise<ApplicationDetail> => {
  if (isMockMode()) {
    await delay(250);

    const index = mockApplications.findIndex((item) => item.id === id);

    if (index === -1) {
      throw new Error("Заявка не найдена");
    }

    const current = mockApplications[index];

    const updated: ApplicationDetail = {
      ...current,
      contact_email: payload.contact_email,
      cover_letter: payload.cover_letter,
      applicant: {
        id: current.applicant?.id,
        full_name: payload.full_name,
        phone: payload.phone,
        city: payload.city,
        age: payload.age,
        gender: payload.gender,
        disability_category: payload.disability_category,
      },
    };

    mockApplications[index] = updated;

    return structuredClone(updated);
  }

  return apiRequest<ApplicationDetail>(`/api/applications/${id}/`, {
    method: "PUT",
    json: payload,
  });
};

export const updateApplicationLine = async (
  payload: ApplicationLineUpdatePayload,
): Promise<ApplicationLine> => {
  if (isMockMode()) {
    await delay(200);

    const draft = findMockDraft();

    if (!draft) {
      throw new Error("Черновая заявка не найдена");
    }

    const line = draft.lines.find(
      (item) => item.vacancy.id === payload.vacancy_id,
    );

    if (!line) {
      throw new Error("Строка заявки не найдена");
    }

    if (payload.qty !== undefined) {
      line.qty = payload.qty;
    }

    if (payload.comment !== undefined) {
      line.comment = payload.comment;
    }

    if (payload.is_main !== undefined) {
      line.is_main = payload.is_main;
    }

    if (payload.order_index !== undefined) {
      line.order_index = payload.order_index;
    }

    line.line_salary_total = line.qty * line.vacancy.salary;
    line.calculated_result = line.line_salary_total;

    return structuredClone(line);
  }

  return apiRequest<ApplicationLine>("/api/application-lines/", {
    method: "PUT",
    json: payload,
  });
};

export const deleteApplicationLine = async (
  vacancyId: number,
): Promise<void> => {
  if (isMockMode()) {
    await delay(200);

    const draft = findMockDraft();

    if (!draft) {
      throw new Error("Черновая заявка не найдена");
    }

    draft.lines = draft.lines.filter((line) => line.vacancy.id !== vacancyId);

    return;
  }

  await apiRequest<void>("/api/application-lines/", {
    method: "DELETE",
    json: {
      vacancy_id: vacancyId,
    },
  });
};

export const formApplication = async (
  id: number,
): Promise<ApplicationDetail> => {
  if (isMockMode()) {
    await delay(250);

    const index = mockApplications.findIndex((item) => item.id === id);

    if (index === -1) {
      throw new Error("Заявка не найдена");
    }

    const current = recalcMockApplication(mockApplications[index]);

    if (!current.applicant?.full_name || !current.applicant.phone || !current.applicant.city) {
      throw new Error("Перед формированием заполните ФИО, телефон и город");
    }

    if (!current.lines.length) {
      throw new Error("Нельзя сформировать пустую заявку");
    }

    const updated: ApplicationDetail = {
      ...current,
      status: "FORMED",
      formed_at: new Date().toISOString(),
      estimated_response_date: new Date(
        Date.now() + current.lines.length * 3 * 24 * 60 * 60 * 1000,
      )
        .toISOString()
        .slice(0, 10),
    };

    mockApplications[index] = updated;

    return structuredClone(updated);
  }

  return apiRequest<ApplicationDetail>(`/api/applications/${id}/form/`, {
    method: "PUT",
    json: {},
  });
};

export const moderateApplication = async (
  id: number,
  payload: ApplicationModerationPayload,
): Promise<ApplicationDetail> => {
  if (isMockMode()) {
    await delay(250);

    const index = mockApplications.findIndex((item) => item.id === id);

    if (index === -1) {
      throw new Error("Заявка не найдена");
    }

    const updated: ApplicationDetail = {
      ...mockApplications[index],
      status: payload.action === "finish" ? "FINISHED" : "REJECTED",
      moderator_note: payload.moderator_note,
      completed_at: new Date().toISOString(),
      moderator_login: "moderator",
    };

    mockApplications[index] = updated;

    return structuredClone(updated);
  }

  return apiRequest<ApplicationDetail>(`/api/applications/${id}/moderate/`, {
    method: "PUT",
    json: payload,
  });
};

export const deleteApplication = async (id: number): Promise<void> => {
  if (isMockMode()) {
    await delay(200);

    mockApplications = mockApplications.map((application) =>
      application.id === id
        ? {
            ...application,
            status: "DELETED",
          }
        : application,
    );

    return;
  }

  await apiRequest<void>(`/api/applications/${id}/delete/`, {
    method: "DELETE",
  });
};
