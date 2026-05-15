import { useEffect, useState } from "react";
import { Alert, Spinner } from "react-bootstrap";
import { Link } from "react-router-dom";

import {
  fetchApplicantCabinet,
  updateApplicantProfile,
} from "../api/cabinetApi";

import { ROUTES } from "../routes";

import {
  APPLICATION_STATUS_LABELS,
  DISABILITY_CATEGORY_LABELS,
  GENDER_LABELS,
  type ApplicantProfile,
  type ApplicationListItem,
  type DisabilityCategory,
  type Gender,
} from "../types/application";
import type { CurrentUser } from "../types/auth";

interface ApplicantCabinetPageProps {
  user: CurrentUser;
}

export const ApplicantCabinetPage = ({ user }: ApplicantCabinetPageProps) => {
  const [profile, setProfile] = useState<ApplicantProfile | null>(null);
  const [draftId, setDraftId] = useState<number | null>(null);
  const [lastApplications, setLastApplications] = useState<ApplicationListItem[]>(
    [],
  );

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let ignore = false;

    const loadCabinet = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await fetchApplicantCabinet(user);

        if (!ignore) {
          setProfile(data.profile);
          setDraftId(data.draftId);
          setLastApplications(data.lastApplications);
        }
      } catch (err) {
        if (!ignore) {
          setError(
            err instanceof Error
              ? err.message
              : "Не удалось загрузить кабинет соискателя",
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

  const updateField = (field: keyof ApplicantProfile, value: string) => {
    setProfile((current) => {
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

  const handleSaveProfile = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!profile) {
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const updated = await updateApplicantProfile(profile, draftId);

      setProfile(updated);
      setSuccess("Профиль сохранён");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось сохранить профиль",
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="empty">
        <Spinner animation="border" size="sm" /> Загрузка кабинета...
      </div>
    );
  }

  if (!profile) {
    return <div className="empty">Профиль не найден</div>;
  }

  return (
    <>
      <section className="hero-card">
        <div>
          <span className="eyebrow">Кабинет соискателя</span>
          <h1 className="page-title">Ваш профиль и отклики</h1>
          <p className="muted">
            Заполните данные профиля и откликайтесь на опубликованные вакансии.
          </p>
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

      <div className="cabinet-grid">
        <section className="glass-card">
          <h2>Личные данные</h2>

          <form className="profile-form" onSubmit={handleSaveProfile}>
            <div className="field-row">
              <div className="field">
                <label>ФИО</label>
                <input
                  value={profile.full_name}
                  disabled={saving}
                  onChange={(event) =>
                    updateField("full_name", event.target.value)
                  }
                />
              </div>

              <div className="field">
                <label>Телефон</label>
                <input
                  value={profile.phone}
                  disabled={saving}
                  onChange={(event) => updateField("phone", event.target.value)}
                />
              </div>
            </div>

            <div className="field-row">
              <div className="field">
                <label>Город</label>
                <input
                  value={profile.city}
                  disabled={saving}
                  onChange={(event) => updateField("city", event.target.value)}
                />
              </div>

              <div className="field">
                <label>Возраст</label>
                <input
                  value={profile.age ?? ""}
                  disabled={saving}
                  onChange={(event) => updateField("age", event.target.value)}
                />
              </div>
            </div>

            <div className="field-row">
              <div className="field">
                <label>Пол</label>
                <select
                  value={profile.gender}
                  disabled={saving}
                  onChange={(event) =>
                    updateField("gender", event.target.value as Gender)
                  }
                >
                  {Object.entries(GENDER_LABELS).map(([code, label]) => (
                    <option value={code} key={code}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label>Категория инвалидности</label>
                <select
                  value={profile.disability_category}
                  disabled={saving}
                  onChange={(event) =>
                    updateField(
                      "disability_category",
                      event.target.value as DisabilityCategory,
                    )
                  }
                >
                  {Object.entries(DISABILITY_CATEGORY_LABELS).map(
                    ([code, label]) => (
                      <option value={code} key={code}>
                        {label}
                      </option>
                    ),
                  )}
                </select>
              </div>
            </div>

            <button className="btn" type="submit" disabled={saving}>
              {saving ? "Сохранение..." : "Сохранить профиль"}
            </button>
          </form>
        </section>

        <section className="glass-card">
          <h2>Быстрые действия</h2>

          <div className="action-stack">
            <Link className="action-link" to={ROUTES.VACANCIES}>
              Открыть вакансии
            </Link>

            <Link className="action-link" to={ROUTES.APPLICATIONS}>
              Мои заявки
            </Link>

            {draftId && (
              <Link className="action-link" to={`/applications/${draftId}`}>
                Открыть черновик заявки №{draftId}
              </Link>
            )}
          </div>

          <h2 style={{ marginTop: 26 }}>Последние заявки</h2>

          <div className="list-stack">
            {lastApplications.length > 0 ? (
              lastApplications.map((application) => (
                <Link
                  className="list-card"
                  to={`/applications/${application.id}`}
                  key={application.id}
                >
                  <strong>Заявка №{application.id}</strong>
                  <span>
                    Статус: {APPLICATION_STATUS_LABELS[application.status]}
                  </span>
                </Link>
              ))
            ) : (
              <div className="list-card list-card--static">
                <strong>Заявок пока нет</strong>
                <span>Выберите вакансию и откликнитесь на неё.</span>
              </div>
            )}
          </div>
        </section>
      </div>
    </>
  );
};
