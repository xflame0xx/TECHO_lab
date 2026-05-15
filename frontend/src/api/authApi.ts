import { apiRequest, isMockMode } from "./apiClient";
import type {
  CurrentUser,
  LoginPayload,
  RegisterPayload,
  UserRole,
} from "../types/auth";

let mockUser: CurrentUser | null = null;

const getMockRoleByUsername = (username: string): UserRole => {
  const value = username.trim().toLowerCase();

  if (
    value.includes("moderator") ||
    value.includes("admin") ||
    value.includes("ilya")
  ) {
    return "moderator";
  }

  if (
    value.includes("employer") ||
    value.includes("company") ||
    value.includes("hr")
  ) {
    return "employer";
  }

  return "applicant";
};

const buildMockUser = (
  username: string,
  role: UserRole,
  extra?: Partial<CurrentUser>,
): CurrentUser => {
  return {
    id: role === "moderator" ? 1 : role === "employer" ? 2 : 3,
    username,
    role,
    full_name: extra?.full_name || username,
    email: extra?.email || `${username}@example.com`,
    is_authenticated: true,
    session_key: "mock-session",
  };
};

export const getCurrentUser = async (): Promise<CurrentUser | null> => {
  if (isMockMode()) {
    return mockUser;
  }

  const response = await fetch("/api/users/me/", {
    method: "GET",
    credentials: "include",
  });

  if (response.status === 401 || response.status === 403) {
    return null;
  }

  if (!response.ok) {
    return null;
  }

  return response.json() as Promise<CurrentUser>;
};

export const loginUser = async (
  payload: LoginPayload,
): Promise<CurrentUser> => {
  if (isMockMode()) {
    const role = getMockRoleByUsername(payload.username);
    mockUser = buildMockUser(payload.username, role);
    return mockUser;
  }

  await apiRequest("/api/users/login/", {
    method: "POST",
    json: {
      username: payload.username,
      password: payload.password,
    },
  });

  const user = await getCurrentUser();

  if (!user) {
    throw new Error("Не удалось получить текущего пользователя после входа");
  }

  return user;
};

export const registerUser = async (
  payload: RegisterPayload,
): Promise<void> => {
  if (isMockMode()) {
    mockUser = null;
    return;
  }

  await apiRequest("/api/users/register/", {
    method: "POST",
    json: payload,
  });

  /*
    Если backend после регистрации автоматически авторизовал пользователя,
    сразу выполняем logout. Так после регистрации пользователь должен войти вручную.
  */
  try {
    await apiRequest("/api/users/logout/", {
      method: "POST",
    });
  } catch {
    // Если backend не авторизует пользователя после регистрации,
    // logout может вернуть ошибку. Это не критично.
  }
};

export const logoutUser = async (): Promise<void> => {
  if (isMockMode()) {
    mockUser = null;
    return;
  }

  await apiRequest("/api/users/logout/", {
    method: "POST",
  });
};
