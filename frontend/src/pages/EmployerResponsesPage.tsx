import { useEffect, useState } from "react";
import { Alert, Spinner } from "react-bootstrap";
import { Link } from "react-router-dom";

import { fetchEmployerResponses } from "../api/cabinetApi";
import { ROUTES } from "../routes";
import {
  APPLICATION_STATUS_LABELS,
  type ApplicationListItem,
} from "../types/application";
import type { CurrentUser } from "../types/auth";

interface EmployerResponsesPageProps {
  user: CurrentUser;
}

export const EmployerResponsesPage = ({ user }: EmployerResponsesPageProps) => {
  const [applications, setApplications] = useState<ApplicationListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;

    const loadResponses = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await fetchEmployerResponses();

        if (!ignore) {
          setApplications(data.applications);
        }
      } catch (err) {
        if (!ignore) {
          setError(
            err instanceof Error
              ? err.message
              : "Не удалось загрузить отклики",
          );
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    loadResponses();

    return () => {
      ignore = true;
    };
  }, [user]);

  return (
    <>
      <section className="hero-card">
        <div>
          <span className="eyebrow">Работодатель</span>
          <h1 className="page-title">Отклики на ваши вакансии</h1>
        </div>

        <div>
          <Link className="btn btn-ghost" to={ROUTES.EMPLOYER_CABINET}>
            ← Назад в кабинет
          </Link>
        </div>
      </section>

      {error && (
        <Alert variant="danger" style={{ marginBottom: 20 }}>
          {error}
        </Alert>
      )}

      <section className="glass-card">
        {loading ? (
          <div className="empty">
            <Spinner animation="border" size="sm" /> Загрузка откликов...
          </div>
        ) : (
          <div className="list-stack">
            {applications.length > 0 ? (
              applications.map((application) => (
                <div className="list-card list-card--static" key={application.id}>
                  <strong>Заявка №{application.id}</strong>
                  <span>
                    Соискатель:{" "}
                    {application.applicant_name ||
                      application.creator_login ||
                      "—"}
                  </span>
                  <span>
                    Статус: {APPLICATION_STATUS_LABELS[application.status]}
                  </span>
                  <span>Позиции: {application.lines_count || 0}</span>
                  <span>
                    Сумма:{" "}
                    {(application.total_sum || application.total_salary || 0)
                      .toLocaleString("ru-RU")}{" "}
                    ₽
                  </span>
                </div>
              ))
            ) : (
              <div className="list-card list-card--static">
                <strong>Откликов пока нет</strong>
                <span>
                  Когда соискатели начнут откликаться, они появятся здесь.
                </span>
              </div>
            )}
          </div>
        )}
      </section>
    </>
  );
};
