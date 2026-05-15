import { useEffect, useState } from "react";
import { Alert, Spinner } from "react-bootstrap";

import {
  EMPTY_VACANCY_FILTERS,
  type Vacancy,
  type VacancyFilters as VacancyFiltersType,
} from "../types/vacancy";

import type { ApplicationCart } from "../types/application";
import type { CurrentUser } from "../types/auth";

import { fetchVacancies } from "../api/vacancyApi";
import {
  addVacancyToApplication,
  fetchApplicationCart,
} from "../api/applicationApi";

import { DraftApplicationCard } from "../components/DraftApplicationCard";
import { VacancyCard } from "../components/VacancyCard";
import { VacancyFilters } from "../components/VacancyFilters";

interface VacanciesPageProps {
  user: CurrentUser | null;
}

export const VacanciesPage = ({ user }: VacanciesPageProps) => {
  const [filters, setFilters] =
    useState<VacancyFiltersType>(EMPTY_VACANCY_FILTERS);

  const [appliedFilters, setAppliedFilters] =
    useState<VacancyFiltersType>(EMPTY_VACANCY_FILTERS);

  const [vacancies, setVacancies] = useState<Vacancy[]>([]);
  const [cart, setCart] = useState<ApplicationCart | null>(null);

  const [loading, setLoading] = useState(false);
  const [cartLoading, setCartLoading] = useState(false);
  const [addingVacancyId, setAddingVacancyId] = useState<number | null>(null);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let ignore = false;

    const loadVacancies = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await fetchVacancies(appliedFilters);

        if (!ignore) {
          setVacancies(data);
        }
      } catch (err) {
        if (!ignore) {
          setError(
            err instanceof Error ? err.message : "Не удалось загрузить вакансии",
          );
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    loadVacancies();

    return () => {
      ignore = true;
    };
  }, [appliedFilters]);

  useEffect(() => {
    let ignore = false;

    const loadCart = async () => {
      if (!user || user.role !== "applicant") {
        setCart(null);
        return;
      }

      try {
        setCartLoading(true);

        const data = await fetchApplicationCart();

        if (!ignore) {
          setCart(data);
        }
      } finally {
        if (!ignore) {
          setCartLoading(false);
        }
      }
    };

    loadCart();

    return () => {
      ignore = true;
    };
  }, [user]);

  const handleSubmitFilters = () => {
    setAppliedFilters(filters);
  };

  const handleResetFilters = () => {
    setFilters(EMPTY_VACANCY_FILTERS);
    setAppliedFilters(EMPTY_VACANCY_FILTERS);
  };

  const handleAddToApplication = async (vacancyId: number) => {
    try {
      setAddingVacancyId(vacancyId);
      setError("");
      setSuccess("");

      const response = await addVacancyToApplication(vacancyId);

      setCart((current) => ({
        application_id: response.application_id,
        items_count: current ? current.items_count + 1 : 1,
      }));

      setSuccess("Вакансия добавлена в текущую заявку");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось добавить вакансию в заявку",
      );
    } finally {
      setAddingVacancyId(null);
    }
  };

  return (
    <>
      <h1 className="page-title">Вакансии для соискателей</h1>

      <VacancyFilters
        filters={filters}
        loading={loading}
        onChange={setFilters}
        onSubmit={handleSubmitFilters}
        onReset={handleResetFilters}
      />

      {cartLoading ? (
        <div className="draft-empty">Загрузка текущей заявки...</div>
      ) : (
        <DraftApplicationCard user={user} cart={cart} />
      )}

      {error && (
        <Alert variant="danger" style={{ marginBottom: 20 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert variant="success" style={{ marginBottom: 20 }}>
          {success}
        </Alert>
      )}

      {loading && (
        <div className="empty">
          <Spinner animation="border" size="sm" /> Загрузка вакансий...
        </div>
      )}

      {!loading && vacancies.length > 0 && (
        <div className="grid">
          {vacancies.map((vacancy) => (
            <VacancyCard
              key={vacancy.id}
              vacancy={vacancy}
              user={user}
              adding={addingVacancyId === vacancy.id}
              onAddToApplication={handleAddToApplication}
            />
          ))}
        </div>
      )}

      {!loading && vacancies.length === 0 && (
        <div className="empty">Ничего не найдено.</div>
      )}
    </>
  );
};
