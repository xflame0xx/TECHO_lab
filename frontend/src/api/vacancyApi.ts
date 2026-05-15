import { apiRequest, isMockMode } from "./apiClient";
import { MOCK_VACANCIES } from "../data/mockVacancies";
import type { Vacancy, VacancyFilters } from "../types/vacancy";

const delay = async (ms: number) => {
  return new Promise<void>((resolve) => {
    window.setTimeout(resolve, ms);
  });
};

const normalizeVacancy = (vacancy: Vacancy): Vacancy => {
  return {
    ...vacancy,
    salary: Number(vacancy.salary || 0),
    description: vacancy.description || "",
    schedule: vacancy.schedule || "",
    disability_support: vacancy.disability_support || "",
    image_url: vacancy.image_url || null,
    video_url: vacancy.video_url || null,
    published_at: vacancy.published_at || null,
  };
};

const isDateInRange = (
  publishedAt: string | null,
  dateFrom: string,
  dateTo: string,
): boolean => {
  if (!dateFrom && !dateTo) {
    return true;
  }

  if (!publishedAt) {
    return false;
  }

  const publishedDate = new Date(publishedAt);
  const fromDate = dateFrom ? new Date(`${dateFrom}T00:00:00`) : null;
  const toDate = dateTo ? new Date(`${dateTo}T23:59:59`) : null;

  if (fromDate && publishedDate < fromDate) {
    return false;
  }

  if (toDate && publishedDate > toDate) {
    return false;
  }

  return true;
};

export const filterVacancies = (
  vacancies: Vacancy[],
  filters: VacancyFilters,
): Vacancy[] => {
  const search = filters.search.trim().toLowerCase();
  const minPrice = filters.minPrice ? Number(filters.minPrice) : null;
  const maxPrice = filters.maxPrice ? Number(filters.maxPrice) : null;

  return vacancies.filter((item) => {
    const vacancy = normalizeVacancy(item);

    const matchesSearch =
      !search ||
      vacancy.title.toLowerCase().includes(search) ||
      vacancy.company.toLowerCase().includes(search) ||
      vacancy.city.toLowerCase().includes(search) ||
      vacancy.description.toLowerCase().includes(search);

    const matchesMinPrice = minPrice === null || vacancy.salary >= minPrice;
    const matchesMaxPrice = maxPrice === null || vacancy.salary <= maxPrice;

    const matchesDate = isDateInRange(
      vacancy.published_at,
      filters.dateFrom,
      filters.dateTo,
    );

    return matchesSearch && matchesMinPrice && matchesMaxPrice && matchesDate;
  });
};

const buildVacancyQuery = (filters: VacancyFilters): string => {
  const params = new URLSearchParams();

  if (filters.search.trim()) {
    params.set("search", filters.search.trim());
  }

  if (filters.minPrice.trim()) {
    params.set("min_price", filters.minPrice.trim());
  }

  if (filters.maxPrice.trim()) {
    params.set("max_price", filters.maxPrice.trim());
  }

  if (filters.dateFrom) {
    params.set("date_from", filters.dateFrom);
  }

  if (filters.dateTo) {
    params.set("date_to", filters.dateTo);
  }

  const queryString = params.toString();

  return queryString ? `/api/vacancies/?${queryString}` : "/api/vacancies/";
};

const fetchMockVacancies = async (
  filters: VacancyFilters,
): Promise<Vacancy[]> => {
  await delay(250);

  return filterVacancies(MOCK_VACANCIES, filters).map(normalizeVacancy);
};

export const fetchVacancies = async (
  filters: VacancyFilters,
): Promise<Vacancy[]> => {
  if (isMockMode()) {
    return fetchMockVacancies(filters);
  }

  try {
    const data = await apiRequest<Vacancy[]>(buildVacancyQuery(filters));

    return data.map(normalizeVacancy);
  } catch (error) {
    console.warn(
      "Backend недоступен. Для списка вакансий используются mock-объекты.",
      error,
    );

    return fetchMockVacancies(filters);
  }
};

export const fetchVacancyById = async (id: string): Promise<Vacancy> => {
  if (isMockMode()) {
    await delay(250);

    const vacancy = MOCK_VACANCIES.find((item) => String(item.id) === id);

    if (!vacancy) {
      throw new Error("Вакансия не найдена");
    }

    return normalizeVacancy(vacancy);
  }

  try {
    const vacancy = await apiRequest<Vacancy>(`/api/vacancies/${id}/`);

    return normalizeVacancy(vacancy);
  } catch (error) {
    console.warn(
      "Backend недоступен. Детальная вакансия берётся из mock-объектов.",
      error,
    );

    const vacancy = MOCK_VACANCIES.find((item) => String(item.id) === id);

    if (!vacancy) {
      throw new Error("Вакансия не найдена");
    }

    return normalizeVacancy(vacancy);
  }
};
