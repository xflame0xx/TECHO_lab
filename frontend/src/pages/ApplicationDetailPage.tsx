import { useEffect, useMemo, useState } from "react";
import { Alert, Spinner } from "react-bootstrap";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  deleteApplication,
  deleteApplicationLine,
  fetchApplicationById,
  formApplication,
  moderateApplication,
  updateApplication,
  updateApplicationLine,
} from "../api/applicationApi";

import { ApplicationLineCard } from "../components/ApplicationLineCard";

import { ROUTES } from "../routes";
import type { CurrentUser } from "../types/auth";
import {
  APPLICATION_STATUS_LABELS,
  DISABILITY_CATEGORY_LABELS,
  GENDER_LABELS,
  type ApplicationDetail,
  type ApplicationLine,
  type ApplicationUpdatePayload,
  type DisabilityCategory,
  type Gender,
} from "../types/application";

interface ApplicationDetailPageProps {
  user: CurrentUser | null;
}

const formatDateTime = (value: string | null) => {
  if (!value) {
    return "—";
  }

  return new Date(value).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const buildForm = (application: ApplicationDetail): ApplicationUpdatePayload => {
  return {
    full_name: application.applicant?.full_name || "",
    phone: application.applicant?.phone || "",
    city: application.applicant?.city || "",
    age: application.applicant?.age ?? null,
    gender: application.applicant?.gender || "other",
    disability_category: application.applicant?.disability_category || "none",
    contact_email: application.contact_email || "",
    cover_letter: application.cover_letter || "",
  };
};

export const ApplicationDetailPage = ({ user }: ApplicationDetailPageProps) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [application, setApplication] = useState<ApplicationDetail | null>(null);
  const [form, setForm] = useState<ApplicationUpdatePayload | null>(null);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const isApplicant = user?.role === "applicant";
  const isModerator = user?.role === "moderator";
  const isDraft = application?.status === "DRAFT";
  const editable = isApplicant && isDraft;

  const totalPositions = useMemo(() => {
    return application?.lines.reduce((sum, line) => sum + line.qty, 0) || 0;
  }, [application]);

  const totalSum = useMemo(() => {
    return (
      application?.lines.reduce(
        (sum, line) =>
          sum + (line.line_salary_total ?? line.qty * line.vacancy.salary),
        0,
      ) || 0
    );
  }, [application]);

  useEffect(() => {
    if (!id) {
      setError("ID заявки не указан");
      return;
    }

    let ignore = false;

    const loadApplication = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await fetchApplicationById(id);

        if (!ignore) {
          setApplication(data);
          setForm(buildForm(data));
        }
      } catch (err) {
        if (!ignore) {
          setError(
            err instanceof Error ? err.message : "Не удалось загрузить заявку",
          );
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    loadApplication();

    return () => {
      ignore = true;
    };
  }, [id]);

  const updateFormField = (
    field: keyof ApplicationUpdatePayload,
    value: string,
  ) => {
    setForm((current) => {
      if (!current) {
        return current;
      }

      if (field === "age") {
        return {
          ...current,
          age: value ? Number(value) : null,
        };
      }

      return {
        ...current,
        [field]: value,
      };
    });
  };

  const handleSaveApplication = async () => {
    if (!application || !form) {
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const updated = await updateApplication(application.id, form);

      setApplication(updated);
      setForm(buildForm(updated));
      setSuccess("Заявка сохранена");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить заявку");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveLine = async (
    line: ApplicationLine,
    qty: number,
    comment: string,
  ) => {
    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const updatedLine = await updateApplicationLine({
        vacancy_id: line.vacancy.id,
        qty,
        comment,
        is_main: line.is_main,
        order_index: line.order_index,
      });

      setApplication((current) => {
        if (!current) {
          return current;
        }

        return {
          ...current,
          lines: current.lines.map((item) =>
            item.vacancy.id === updatedLine.vacancy.id ? updatedLine : item,
          ),
        };
      });

      setSuccess("Строка заявки сохранена");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить строку");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteLine = async (line: ApplicationLine) => {
    const confirmed = window.confirm("Удалить вакансию из заявки?");

    if (!confirmed) {
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      await deleteApplicationLine(line.vacancy.id);

      setApplication((current) => {
        if (!current) {
          return current;
        }

        return {
          ...current,
          lines: current.lines.filter(
            (item) => item.vacancy.id !== line.vacancy.id,
          ),
        };
      });

      setSuccess("Строка удалена");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось удалить строку");
    } finally {
      setSaving(false);
    }
  };

  const handleFormApplication = async () => {
    if (!application) {
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const updated = await formApplication(application.id);

      setApplication(updated);
      setForm(buildForm(updated));
      setSuccess("Заявка сформирована");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сформировать заявку");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteApplication = async () => {
    if (!application) {
      return;
    }

    const confirmed = window.confirm("Удалить заявку?");

    if (!confirmed) {
      return;
    }

    try {
      setSaving(true);
      setError("");

      await deleteApplication(application.id);

      navigate(ROUTES.APPLICATIONS);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось удалить заявку");
    } finally {
      setSaving(false);
    }
  };

  const handleModerate = async (action: "finish" | "reject") => {
    if (!application) {
      return;
    }

    const note = window.prompt(
      action === "finish"
        ? "Комментарий модератора при завершении"
        : "Причина отклонения",
      application.moderator_note || "",
    );

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const updated = await moderateApplication(application.id, {
        action,
        moderator_note: note || "",
      });

      setApplication(updated);
      setForm(buildForm(updated));
      setSuccess(
        action === "finish" ? "Заявка завершена" : "Заявка отклонена",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось обработать заявку");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="ja-empty">
        <Spinner animation="border" size="sm" /> Загрузка заявки...
      </div>
    );
  }

  if (error && !application) {
    return <div className="ja-empty">{error}</div>;
  }

  if (!application || !form) {
    return <div className="ja-empty">Заявка не найдена</div>;
  }

  return (
    <section className="ja-application-detail">
      <div className="ja-application-detail__header">
        <div>
          <span className="ja-section-label">Заявка</span>

          <h1 className="page-title">Заявка №{application.id}</h1>

          <div className="ja-application-stats">
            <div>
              <span>Создана</span>
              <strong>{formatDateTime(application.created_at)}</strong>
            </div>

            <div>
              <span>Позиции</span>
              <strong>{totalPositions}</strong>
            </div>

            <div>
              <span>Сумма</span>
              <strong>{totalSum.toLocaleString("ru-RU")} ₽</strong>
            </div>

            <div>
              <span>Статус</span>
              <strong>{APPLICATION_STATUS_LABELS[application.status]}</strong>
            </div>
          </div>
        </div>

        <Link className="ja-button ja-button--outline" to={ROUTES.APPLICATIONS}>
          К списку заявок
        </Link>
      </div>

      {error && (
        <Alert variant="danger" className="ja-page-alert">
          {error}
        </Alert>
      )}

      {success && (
        <Alert variant="success" className="ja-page-alert">
          {success}
        </Alert>
      )}

      <div className="ja-application-detail__layout">
        <section className="ja-panel-card">
          <h2>Данные заявки</h2>

          <div className="ja-readonly-grid">
            <div className="ja-readonly-box">
              <span>Статус</span>
              <strong>{APPLICATION_STATUS_LABELS[application.status]}</strong>
            </div>

            <div className="ja-readonly-box">
              <span>Дата формирования</span>
              <strong>{formatDateTime(application.formed_at)}</strong>
            </div>

            <div className="ja-readonly-box">
              <span>Дата завершения</span>
              <strong>{formatDateTime(application.completed_at)}</strong>
            </div>
          </div>

          <h2>Данные соискателя</h2>

          <div className="ja-form-grid ja-form-grid--three">
            <label className="ja-form-field">
              <span>ФИО</span>
              <input
                disabled={!editable || saving}
                value={form.full_name}
                placeholder="Иванов Иван Иванович"
                onChange={(event) =>
                  updateFormField("full_name", event.target.value)
                }
              />
            </label>

            <label className="ja-form-field">
              <span>Телефон</span>
              <input
                disabled={!editable || saving}
                value={form.phone}
                placeholder="+7 (900) 000-00-00"
                onChange={(event) => updateFormField("phone", event.target.value)}
              />
            </label>

            <label className="ja-form-field">
              <span>Город</span>
              <input
                disabled={!editable || saving}
                value={form.city}
                placeholder="Москва"
                onChange={(event) => updateFormField("city", event.target.value)}
              />
            </label>

            <label className="ja-form-field">
              <span>Возраст</span>
              <input
                disabled={!editable || saving}
                value={form.age ?? ""}
                placeholder="22"
                onChange={(event) => updateFormField("age", event.target.value)}
              />
            </label>

            <label className="ja-form-field">
              <span>Пол</span>
              <select
                disabled={!editable || saving}
                value={form.gender}
                onChange={(event) =>
                  updateFormField("gender", event.target.value as Gender)
                }
              >
                {Object.entries(GENDER_LABELS).map(([code, label]) => (
                  <option value={code} key={code}>
                    {label}
                  </option>
                ))}
              </select>
            </label>

            <label className="ja-form-field">
              <span>Категория инвалидности</span>
              <select
                disabled={!editable || saving}
                value={form.disability_category}
                onChange={(event) =>
                  updateFormField(
                    "disability_category",
                    event.target.value as DisabilityCategory,
                  )
                }
              >
                {Object.entries(DISABILITY_CATEGORY_LABELS).map(([code, label]) => (
                  <option value={code} key={code}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <h2>Контакты</h2>

          <div className="ja-form-grid">
            <label className="ja-form-field">
              <span>Email для связи</span>
              <input
                type="email"
                disabled={!editable || saving}
                value={form.contact_email}
                onChange={(event) =>
                  updateFormField("contact_email", event.target.value)
                }
              />
            </label>

            <label className="ja-form-field">
              <span>Сопроводительное письмо</span>
              <textarea
                disabled={!editable || saving}
                value={form.cover_letter}
                onChange={(event) =>
                  updateFormField("cover_letter", event.target.value)
                }
              />
            </label>
          </div>

          {editable ? (
            <button
              type="button"
              className="ja-button"
              disabled={saving}
              onClick={handleSaveApplication}
            >
              Сохранить данные заявки
            </button>
          ) : (
            <div className="ja-hint-box">
              Редактировать можно только черновик заявки соискателя.
            </div>
          )}
        </section>

        <section className="ja-panel-card">
          <div className="ja-panel-card__head">
            <h2>Состав заявки</h2>
            <span>{application.lines.length} позиций</span>
          </div>

          <div className="ja-application-lines">
            {application.lines.length > 0 ? (
              application.lines.map((line) => (
                <ApplicationLineCard
                  key={line.id}
                  line={line}
                  editable={editable}
                  saving={saving}
                  onSave={handleSaveLine}
                  onDelete={handleDeleteLine}
                />
              ))
            ) : (
              <div className="ja-empty">
                В заявке пока нет вакансий. Перейдите в раздел «Вакансии» и
                добавьте подходящую вакансию.
              </div>
            )}
          </div>

          <div className="ja-application-total">
            <span>Итого</span>
            <strong>{totalSum.toLocaleString("ru-RU")} ₽</strong>
          </div>
        </section>
      </div>

      {editable && (
        <div className="ja-danger-zone">
          <button
            type="button"
            className="ja-button"
            disabled={saving}
            onClick={handleFormApplication}
          >
            Сформировать заявку
          </button>

          <button
            type="button"
            className="ja-button ja-button--danger"
            disabled={saving}
            onClick={handleDeleteApplication}
          >
            Удалить заявку
          </button>
        </div>
      )}

      {isModerator && application.status === "FORMED" && (
        <div className="ja-danger-zone">
          <button
            type="button"
            className="ja-button"
            disabled={saving}
            onClick={() => handleModerate("finish")}
          >
            Завершить заявку
          </button>

          <button
            type="button"
            className="ja-button ja-button--danger"
            disabled={saving}
            onClick={() => handleModerate("reject")}
          >
            Отклонить заявку
          </button>
        </div>
      )}
    </section>
  );
};
