import { useEffect, useState } from "react";
import { Alert, Spinner } from "react-bootstrap";
import { Link, useNavigate, useParams } from "react-router-dom";

import { addVacancyToApplication } from "../api/applicationApi";
import { fetchVacancyById } from "../api/vacancyApi";

import { AppBreadcrumbs } from "../components/AppBreadcrumbs";
import { SimilarVacancies } from "../components/SimilarVacancies";

import { FALLBACK_IMAGE, setFallbackImage } from "../data/imageFallback";

import { ROUTES } from "../routes";
import type { CurrentUser } from "../types/auth";
import type { Vacancy } from "../types/vacancy";

interface VacancyDetailPageProps {
  user: CurrentUser | null;
}

export const VacancyDetailPage = ({ user }: VacancyDetailPageProps) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [vacancy, setVacancy] = useState<Vacancy | null>(null);
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    if (!id) {
      setError("ID вакансии не указан");
      return;
    }

    let ignore = false;

    const loadVacancy = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await fetchVacancyById(id);

        if (!ignore) {
          setVacancy(data);
        }
      } catch (err) {
        if (!ignore) {
          setError(
            err instanceof Error ? err.message : "Не удалось загрузить вакансию",
          );
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    loadVacancy();

    return () => {
      ignore = true;
    };
  }, [id]);

  const handleAddToApplication = async () => {
    if (!vacancy) {
      return;
    }

    if (!user) {
      navigate(ROUTES.LOGIN);
      return;
    }

    if (user.role !== "applicant") {
      setError("Добавлять вакансии в заявку может только соискатель");
      return;
    }

    try {
      setAdding(true);
      setError("");
      setSuccess("");

      await addVacancyToApplication(vacancy.id);

      setSuccess("Вакансия добавлена в текущую заявку");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Не удалось добавить вакансию в заявку",
      );
    } finally {
      setAdding(false);
    }
  };

  if (loading) {
    return (
      <div className="empty">
        <Spinner animation="border" size="sm" /> Загрузка вакансии...
      </div>
    );
  }

  if (error && !vacancy) {
    return <div className="empty">{error}</div>;
  }

  if (!vacancy) {
    return <div className="empty">Вакансия не найдена</div>;
  }

  return (
    <>
      <AppBreadcrumbs
        items={[
          {
            label: vacancy.title,
          },
        ]}
      />

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

      <div className="service-box">
        <div className="service-image">
          <img
            src={vacancy.image_url || FALLBACK_IMAGE}
            alt={vacancy.title}
            loading="lazy"
            decoding="async"
            onError={setFallbackImage}
          />
        </div>

        <div className="service-info">
          <h1>{vacancy.title}</h1>

          <div className="info-list">
            <p>
              <b>Компания:</b> {vacancy.company}
            </p>

            <p>
              <b>Город:</b> {vacancy.city}
            </p>

            <p>
              <b>График:</b> {vacancy.schedule || "—"}
            </p>

            <p>
              <b>Поддержка:</b> {vacancy.disability_support || "—"}
            </p>
          </div>

          {vacancy.description && (
            <div className="description">
              {vacancy.description.split("\n").map((line, index) => (
                <p key={index}>{line}</p>
              ))}
            </div>
          )}

          <div className="buy-row">
            <button
              className="buy-btn"
              type="button"
              disabled={adding || (!!user && user.role !== "applicant")}
              onClick={handleAddToApplication}
            >
              {adding ? "Добавление..." : "В заявку"}
            </button>

            <Link to={ROUTES.VACANCIES} className="buy-btn">
              Назад
            </Link>

            <div className="salary-tag">
              З/п: {vacancy.salary.toLocaleString("ru-RU")} ₽
            </div>
          </div>
        </div>
      </div>

      <SimilarVacancies currentVacancy={vacancy} />
    </>
  );
};
