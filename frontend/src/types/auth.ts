export type UserRole = "applicant" | "employer" | "moderator";

export interface CurrentUser {
  id: number;
  username: string;
  role: UserRole;
  full_name: string;
  email: string;
  is_authenticated?: boolean;
  session_key?: string | null;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  password: string;
  first_name: string;
  last_name: string;
  email: string;
  role: Exclude<UserRole, "moderator">;
}

export const ROLE_LABELS: Record<UserRole, string> = {
  applicant: "Соискатель",
  employer: "Работодатель",
  moderator: "Модератор",
};
