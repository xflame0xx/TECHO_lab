export type VacancyModerationStatus = "PENDING" | "APPROVED" | "REJECTED";

export interface Vacancy {
  id: number;
  title: string;
  company: string;
  city: string;
  salary: number;
  description: string;
  is_active: boolean;
  disability_support: string;
  schedule: string;
  image_url: string | null;
  video_url: string | null;
  creator_login?: string | null;
  moderator_login?: string | null;
  moderation_status?: VacancyModerationStatus;
  moderation_note?: string;
  published_at: string | null;
  is_published?: boolean;
}

export interface VacancyFilters {
  search: string;
  minPrice: string;
  maxPrice: string;
  dateFrom: string;
  dateTo: string;
}

export const EMPTY_VACANCY_FILTERS: VacancyFilters = {
  search: "",
  minPrice: "",
  maxPrice: "",
  dateFrom: "",
  dateTo: "",
};

export const VACANCY_MODERATION_STATUS_LABELS: Record<
  VacancyModerationStatus,
  string
> = {
  PENDING: "На модерации",
  APPROVED: "Одобрена",
  REJECTED: "Отклонена",
};

export interface VacancyCreatePayload {
  title: string;
  company: string;
  city: string;
  salary: string;
  schedule: string;
  disability_support: string;
  description: string;
  image: File | null;
  video: File | null;
}
