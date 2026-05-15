import { useEffect, useState } from "react";
import { Alert, Spinner } from "react-bootstrap";

import { fetchApplications } from "../api/applicationApi";
import { ApplicationFilters } from "../components/ApplicationFilters";
import { ApplicationListCard } from "../components/ApplicationListCard";

import {
  EMPTY_APPLICATION_FILTERS,
  type ApplicationFilters as ApplicationFiltersType,
  type ApplicationListItem,
} from "../types/application";
import type { CurrentUser } from "../types/auth";

interface ApplicationsPageProps {
  user: CurrentUser | null;
}

export const ApplicationsPage = ({ user }: ApplicationsPageProps) => {
  const [filters, setFilters] =
    useState<ApplicationFiltersType>(EMPTY_APPLICATION_FILTERS);

  const [appliedFilters, setAppliedFilters] =
    useState<ApplicationFiltersType>(EMPTY_APPLICATION_FILTERS);

  const [applications, setApplications] = useState<ApplicationListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;

    const loadApplications = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await fetchApplications(appliedFilters);

        if (!ignore) {
          setApplications(data);
        }
      } catch (err) {
        if (!ignore) {
          setError(
            err instanceof Error ? err.message : "Не удалось загрузить заявки",
          );
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    loadApplications();

    return () => {
      ignore = true;
    };
  }, [appliedFilters]);

  const handleSubmitFilters = () => {
    setAppliedFilters(filters);
  };

  const handleResetFilters = () => {
    setFilters(EMPTY_APPLICATION_FILTERS);
    setAppliedFilters(EMPTY_APPLICATION_FILTERS);
  };

  return (
    <section className="ja-page-section">
      <div className="ja-page-head">
        <span className="ja-section-label">Заявки</span>

        <h1 className="page-title">
          {user?.role === "moderator" ? "Все заявки" : "Мои заявки"}
        </h1>

        <p>
          Здесь отображаются заявки, их статусы, даты обработки и итоговые суммы.
        </p>
      </div>

      <ApplicationFilters
        filters={filters}
        loading={loading}
        onChange={setFilters}
        onSubmit={handleSubmitFilters}
        onReset={handleResetFilters}
      />

      {error && (
        <Alert variant="danger" className="ja-page-alert">
          {error}
        </Alert>
      )}

      {loading && (
        <div className="ja-empty">
          <Spinner animation="border" size="sm" /> Загрузка заявок...
        </div>
      )}

      {!loading && applications.length > 0 && (
        <div className="ja-application-list">
          {applications.map((application) => (
            <ApplicationListCard
              key={application.id}
              application={application}
            />
          ))}
        </div>
      )}

      {!loading && applications.length === 0 && (
        <div className="ja-empty">Заявок нет</div>
      )}
    </section>
  );
};
