import type { Vacancy } from "./vacancy";

export type ApplicationStatus =
  | "DRAFT"
  | "FORMED"
  | "FINISHED"
  | "REJECTED"
  | "DELETED";

export type Gender = "male" | "female" | "other";
export type DisabilityCategory = "none" | "I" | "II" | "III";

export interface ApplicantProfile {
  id?: number;
  full_name: string;
  phone: string;
  city: string;
  age: number | null;
  gender: Gender;
  disability_category: DisabilityCategory;
}

export interface ApplicationLine {
  id: number;
  vacancy: Vacancy;
  qty: number;
  comment: string;
  is_main: boolean;
  order_index: number;
  line_salary_total: number | null;
  calculated_result: number;
}

export interface ApplicationListItem {
  id: number;
  status: ApplicationStatus;
  creator_login: string;
  moderator_login: string | null;
  applicant_name: string | null;
  created_at: string;
  formed_at: string | null;
  completed_at: string | null;
  contact_email: string;
  estimated_response_date: string | null;
  total_salary: number;
  lines_count: number;
  calculated_lines_count: number;
  total_sum: number;
}

export interface ApplicationDetail {
  id: number;
  status: ApplicationStatus;
  creator_login: string;
  moderator_login: string | null;
  created_at: string;
  formed_at: string | null;
  completed_at: string | null;
  contact_email: string;
  cover_letter: string;
  estimated_response_date: string | null;
  moderator_note: string;
  total_salary: number;
  applicant: ApplicantProfile | null;
  lines: ApplicationLine[];
}

export interface ApplicationCart {
  application_id: number | null;
  items_count: number;
}

export interface AddVacancyToApplicationResponse {
  application_id: number;
  line: ApplicationLine;
}

export interface ApplicationFilters {
  status: string;
  dateFrom: string;
  dateTo: string;
}

export interface ApplicationUpdatePayload {
  full_name: string;
  phone: string;
  city: string;
  age: number | null;
  gender: Gender;
  disability_category: DisabilityCategory;
  contact_email: string;
  cover_letter: string;
}

export interface ApplicationLineUpdatePayload {
  vacancy_id: number;
  qty?: number;
  comment?: string;
  is_main?: boolean;
  order_index?: number;
}

export interface ApplicationModerationPayload {
  action: "finish" | "reject";
  moderator_note: string;
}

export const EMPTY_APPLICATION_FILTERS: ApplicationFilters = {
  status: "",
  dateFrom: "",
  dateTo: "",
};

export const APPLICATION_STATUS_LABELS: Record<ApplicationStatus, string> = {
  DRAFT: "Черновик",
  FORMED: "Сформирована",
  FINISHED: "Завершена",
  REJECTED: "Отклонена",
  DELETED: "Удалена",
};

export const GENDER_LABELS: Record<Gender, string> = {
  male: "Мужчина",
  female: "Женщина",
  other: "Другое",
};

export const DISABILITY_CATEGORY_LABELS: Record<DisabilityCategory, string> = {
  none: "Нет",
  I: "I группа",
  II: "II группа",
  III: "III группа",
};
