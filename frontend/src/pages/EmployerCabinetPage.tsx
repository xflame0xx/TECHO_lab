import { useEffect, useState } from "react";
import { Alert, Spinner } from "react-bootstrap";
import { Link } from "react-router-dom";

import {
  createEmployerVacancy,
  fetchEmployerCabinet,
} from "../api/cabinetApi";

import { ROUTES } from "../routes";
import type { CurrentUser } from "../types/auth";
import type {
  Vacancy,
  VacancyCreatePayload,
} from "../types/vacancy";
import { VACANCY_MODERATION_STATUS_LABELS } from "../types/vacancy";

interface EmployerCabinetPageProps {
  user: CurrentUser;
}

const EMPTY_FORM: VacancyCreatePayload = {
  title: "",
  company: "",
  city: "",
  salary: "",
  schedule: "",
  disability_support: "",
  description: "",
  image: null,
  video: null,
};

export const EmployerCabinetPage = ({ user }: EmployerCabinetPageProps) => {
  const [form, setForm] = useState<VacancyCreatePayload>(EMPTY_FORM);
  const [vacancies, setVacancies] = useState<Vacancy[]>([]);

  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let ignore = false;

    const loadCabinet = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await fetchEmployerCabinet();

        if (!ignore) {
          setVacancies(data.vacancies);
        }
      } catch (err) {
        if (!ignore) {
          setError(
            err instanceof Error
              ? err.message
              : "Не удалось загрузить кабинет работодателя",
          );
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    loadCabinet();

    return () => {
      ignore = true;
    };
  }, [user]);

  const updateField = (
    field: keyof VacancyCreatePayload,
    value: string | File | null,
  ) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleCreateVacancy = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    try {
      setCreating(true);
      setError("");
      setSuccess("");

      const created = await createEmployerVacancy(form);

      setVacancies((current) => [created, ...current]);
      setForm(EMPTY_FORM);
      setSuccess("Вакансия отправлена на модерацию");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось создать вакансию",
      );
    } finally {
      setCreating(false);
    }
  };

  return (
    <>
      <section className="hero-card">
        <div>
          <span className="eyebrow">Кабинет работодателя</span>
          <h1 className="page-title">Создавайте вакансии и смотрите отклики</h1>
          <p className="muted">
            Каждая новая вакансия сначала отправляется на модерацию.
          </p>
        </div>

        <div>
          <Link className="btn btn-ghost" to={ROUTES.EMPLOYER_RESPONSES}>
            Отклики на мои вакансии
          </Link>
        </div>
      </section>

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
          <Spinner animation="border" size="sm" /> Загрузка кабинета...
        </div>
      )}

      <div className="cabinet-grid cabinet-grid--wide">
        <section className="glass-card">
          <h2>Новая вакансия</h2>

          <form
            className="profile-form"
            onSubmit={handleCreateVacancy}
            encType="multipart/form-data"
          >
            <div className="field-row">
              <div className="field">
                <label>Название вакансии</label>
                <input
                  required
                  value={form.title}
                  disabled={creating}
                  onChange={(event) => updateField("title", event.target.value)}
                />
              </div>

              <div className="field">
                <label>Компания</label>
                <input
                  required
                  value={form.company}
                  disabled={creating}
                  onChange={(event) =>
                    updateField("company", event.target.value)
                  }
                />
              </div>
            </div>

            <div className="field-row">
              <div className="field">
                <label>Город</label>
                <input
                  required
                  value={form.city}
                  disabled={creating}
                  onChange={(event) => updateField("city", event.target.value)}
                />
              </div>

              <div className="field">
                <label>Зарплата</label>
                <input
                  required
                  type="number"
                  min="0"
                  value={form.salary}
                  disabled={creating}
                  onChange={(event) =>
                    updateField("salary", event.target.value)
                  }
                />
              </div>
            </div>

            <div className="field-row">
              <div className="field">
                <label>График</label>
                <input
                  placeholder="Полный день / Гибкий график / Удалённо"
                  value={form.schedule}
                  disabled={creating}
                  onChange={(event) =>
                    updateField("schedule", event.target.value)
                  }
                />
              </div>

              <div className="field">
                <label>Поддержка</label>
                <input
                  placeholder="Адаптированное рабочее место и т.д."
                  value={form.disability_support}
                  disabled={creating}
                  onChange={(event) =>
                    updateField("disability_support", event.target.value)
                  }
                />
              </div>
            </div>

            <div className="field">
              <label>Описание</label>
              <textarea
                rows={5}
                value={form.description}
                disabled={creating}
                onChange={(event) =>
                  updateField("description", event.target.value)
                }
              />
            </div>

            <div className="field-row">
              <div className="field">
                <label>Изображение</label>
                <input
                  type="file"
                  accept="image/*"
                  disabled={creating}
                  onChange={(event) =>
                    updateField("image", event.target.files?.[0] ?? null)
                  }
                />
              </div>

              <div className="field">
                <label>Видео</label>
                <input
                  type="file"
                  accept="video/*"
                  disabled={creating}
                  onChange={(event) =>
                    updateField("video", event.target.files?.[0] ?? null)
                  }
                />
              </div>
            </div>

            <button className="btn" type="submit" disabled={creating}>
              {creating ? "Отправка..." : "Отправить на модерацию"}
            </button>
          </form>
        </section>

        <section className="glass-card">
          <h2>Мои вакансии</h2>

          <div className="list-stack">
            {vacancies.length > 0 ? (
              vacancies.map((vacancy) => (
                <div className="list-card list-card--static" key={vacancy.id}>
                  <strong>{vacancy.title}</strong>
                  <span>
                    {vacancy.company} • {vacancy.city}
                  </span>
                  <small>
                    Статус:{" "}
                    {vacancy.moderation_status
                      ? VACANCY_MODERATION_STATUS_LABELS[
                          vacancy.moderation_status
                        ]
                      : "—"}
                  </small>
                </div>
              ))
            ) : (
              <div className="list-card list-card--static">
                <strong>Пока нет вакансий</strong>
                <span>Создайте первую вакансию через форму слева.</span>
              </div>
            )}
          </div>
        </section>
      </div>
    </>
  );
};
