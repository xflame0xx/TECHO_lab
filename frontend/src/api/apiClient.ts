const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export const isMockMode = () => USE_MOCK;

interface ApiRequestOptions extends RequestInit {
  json?: unknown;
}

export const apiRequest = async <T>(
  url: string,
  options: ApiRequestOptions = {},
): Promise<T> => {
  const headers = new Headers(options.headers);

  if (options.json !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    credentials: "include",
    headers,
    body:
      options.json !== undefined
        ? JSON.stringify(options.json)
        : options.body,
  });

  if (!response.ok) {
    let message = `Ошибка запроса: ${response.status}`;

    try {
      const data = await response.json();
      message = data.detail || JSON.stringify(data);
    } catch {
      // Если ответ сервера не JSON, оставляем стандартный текст ошибки.
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json() as Promise<T>;
};
