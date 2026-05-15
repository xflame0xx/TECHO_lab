import { apiRequest, isMockMode } from "./apiClient";
import { fetchApplications } from "./applicationApi";

import { MOCK_VACANCIES } from "../data/mockVacancies";
import {
  MOCK_APPLICATIONS,
  toApplicationListItem,
} from "../data/mockApplications";

import type { CurrentUser } from "../types/auth";
import type {
  ApplicantProfile,
  ApplicationListItem,
} from "../types/application";
import type {
  Vacancy,
  VacancyCreatePayload,
} from "../types/vacancy";

export interface ApplicantCabinetData {
  profile: ApplicantProfile;
  draftId: number | null;
  lastApplications: ApplicationListItem[];
}

export interface EmployerCabinetData {
  vacancies: Vacancy[];
}

export interface EmployerResponsesData {
  applications: ApplicationListItem[];
}

export interface ModeratorCabinetData {
  pendingVacancies: Vacancy[];
  formedApplications: ApplicationListItem[];
}

let mockProfile: ApplicantProfile = {
  id: 1,
  full_name: "Иванов Иван Иванович",
  phone: "+7 (900) 000-00-00",
  city: "Москва",
  age: 22,
  gender: "male",
  disability_category: "none",
};

let mockEmployerVacancies: Vacancy[] = [
  {
    ...MOCK_VACANCIES[0],
    id: 101,
    title: "Frontend-разработчик React",
    creator_login: "employer",
    moderation_status: "APPROVED",
    is_active: true,
    published_at: "2026-04-10T10:00:00Z",
    is_published: true,
  },
  {
    ...MOCK_VACANCIES[3],
    id: 102,
    title: "UI/UX-дизайнер",
    creator_login: "employer",
    moderation_status: "PENDING",
    is_active: false,
    published_at: null,
    is_published: false,
  },
];

let mockPendingVacancies: Vacancy[] = [
  {
    ...MOCK_VACANCIES[4],
    id: 201,
    title: "Аналитик данных",
    creator_login: "employer",
    moderation_status: "PENDING",
    is_active: false,
    moderation_note: "",
    published_at: null,
    is_published: false,
  },
];

const delay = (ms: number) => {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
};

const buildFormData = (payload: VacancyCreatePayload): FormData => {
  const formData = new FormData();

  formData.append("title", payload.title);
  formData.append("company", payload.company);
  formData.append("city", payload.city);
  formData.append("salary", payload.salary);
  formData.append("schedule", payload.schedule);
  formData.append("disability_support", payload.disability_support);
  formData.append("description", payload.description);

  if (payload.image) {
    formData.append("image", payload.image);
  }

  if (payload.video) {
    formData.append("video", payload.video);
  }

  return formData;
};

export const fetchApplicantCabinet = async (
  user: CurrentUser,
): Promise<ApplicantCabinetData> => {
  if (isMockMode()) {
    await delay(250);

    const lastApplications = MOCK_APPLICATIONS
      .map(toApplicationListItem)
      .slice(0, 5);

    const draft = MOCK_APPLICATIONS.find(
      (application) => application.status === "DRAFT",
    );

    return {
      profile: mockProfile,
      draftId: draft?.id ?? null,
      lastApplications,
    };
  }

  const [profile, applications] = await Promise.all([
    apiRequest<ApplicantProfile>("/api/users/profile/"),
    fetchApplications({
      status: "",
      dateFrom: "",
      dateTo: "",
    }),
  ]);

  const draft = applications.find(
    (application) => application.status === "DRAFT",
  );

  return {
    profile: {
      ...profile,
      full_name: profile.full_name || user.full_name || user.username,
    },
    draftId: draft?.id ?? null,
    lastApplications: applications.slice(0, 5),
  };
};

export const updateApplicantProfile = async (
  profile: ApplicantProfile,
  _draftId: number | null,
): Promise<ApplicantProfile> => {
  if (isMockMode()) {
    await delay(250);

    mockProfile = {
      ...profile,
    };

    return mockProfile;
  }

  return apiRequest<ApplicantProfile>("/api/users/profile/", {
    method: "PUT",
    json: profile,
  });
};

export const fetchEmployerCabinet = async (): Promise<EmployerCabinetData> => {
  if (isMockMode()) {
    await delay(250);

    return {
      vacancies: mockEmployerVacancies,
    };
  }

  const vacancies = await apiRequest<Vacancy[]>("/api/vacancies/mine/");

  return {
    vacancies,
  };
};

export const createEmployerVacancy = async (
  payload: VacancyCreatePayload,
): Promise<Vacancy> => {
  if (isMockMode()) {
    await delay(300);

    const newVacancy: Vacancy = {
      id: Date.now(),
      title: payload.title,
      company: payload.company,
      city: payload.city,
      salary: Number(payload.salary || 0),
      description: payload.description,
      is_active: false,
      disability_support: payload.disability_support,
      schedule: payload.schedule,
      image_url: null,
      video_url: null,
      creator_login: "employer",
      moderator_login: null,
      moderation_status: "PENDING",
      moderation_note: "",
      published_at: null,
      is_published: false,
    };

    mockEmployerVacancies = [newVacancy, ...mockEmployerVacancies];
    mockPendingVacancies = [newVacancy, ...mockPendingVacancies];

    return newVacancy;
  }

  return apiRequest<Vacancy>("/api/vacancies/", {
    method: "POST",
    body: buildFormData(payload),
  });
};

export const fetchEmployerResponses =
  async (): Promise<EmployerResponsesData> => {
    if (isMockMode()) {
      await delay(250);

      return {
        applications: MOCK_APPLICATIONS
          .map(toApplicationListItem)
          .filter((application) => application.status !== "DRAFT"),
      };
    }

    const applications = await apiRequest<ApplicationListItem[]>(
      "/api/applications/employer-responses/",
    );

    return {
      applications,
    };
  };

export const fetchModeratorCabinet =
  async (): Promise<ModeratorCabinetData> => {
    if (isMockMode()) {
      await delay(250);

      return {
        pendingVacancies: mockPendingVacancies,
        formedApplications: MOCK_APPLICATIONS
          .map(toApplicationListItem)
          .filter((application) => application.status === "FORMED"),
      };
    }

    const [pendingVacancies, formedApplications] = await Promise.all([
      apiRequest<Vacancy[]>("/api/vacancies/pending/"),
      fetchApplications({
        status: "FORMED",
        dateFrom: "",
        dateTo: "",
      }),
    ]);

    return {
      pendingVacancies,
      formedApplications,
    };
  };

export const moderateVacancy = async (
  vacancyId: number,
  action: "approve" | "reject",
  moderationNote: string,
): Promise<Vacancy> => {
  if (isMockMode()) {
    await delay(250);

    const vacancy = mockPendingVacancies.find(
      (item) => item.id === vacancyId,
    );

    if (!vacancy) {
      throw new Error("Вакансия не найдена");
    }

    const updatedStatus = action === "approve" ? "APPROVED" : "REJECTED";

    const updatedVacancy: Vacancy = {
      ...vacancy,
      moderation_status: updatedStatus,
      moderation_note: moderationNote,
      is_active: action === "approve",
      moderator_login: "moderator",
      published_at: action === "approve" ? new Date().toISOString() : null,
      is_published: action === "approve",
    };

    mockPendingVacancies = mockPendingVacancies.filter(
      (item) => item.id !== vacancyId,
    );

    mockEmployerVacancies = mockEmployerVacancies.map((item) =>
      item.id === vacancyId ? updatedVacancy : item,
    );

    return updatedVacancy;
  }

  return apiRequest<Vacancy>(`/api/vacancies/${vacancyId}/moderate/`, {
    method: "PUT",
    json: {
      action,
      moderation_note: moderationNote,
    },
  });
};
