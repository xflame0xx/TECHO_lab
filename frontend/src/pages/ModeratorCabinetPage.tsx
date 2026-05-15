import { useEffect, useState } from "react";
import { Alert, Spinner } from "react-bootstrap";

import {
  fetchModeratorCabinet,
  moderateVacancy,
} from "../api/cabinetApi";
import { moderateApplication } from "../api/applicationApi";

import {
  APPLICATION_STATUS_LABELS,
  type ApplicationListItem,
} from "../types/application";
import type { CurrentUser } from "../types/auth";
import type { Vacancy } from "../types/vacancy";

interface ModeratorCabinetPageProps {
  user: CurrentUser;
}

type NotesState = Record<string, string>;

export const ModeratorCabinetPage = ({ user }: ModeratorCabinetPageProps) => {
  const [pendingVacancies, setPendingVacancies] = useState<Vacancy[]>([]);
  const [formedApplications, setFormedApplications] = useState<
    ApplicationListItem[]
  >([]);

  const [notes, setNotes] = useState<NotesState>({});

  const [loading, setLoading] = useState(false);
  const [processingKey, setProcessingKey] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let ignore = false;

    const loadCabinet = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await fetchModeratorCabinet();

        if (!ignore) {
          setPendingVacancies(data.pendingVacancies);
          setFormedApplications(data.formedApplications);
        }
      } catch (err) {
        if (!ignore) {
          setError(
            err instanceof Error
              ? err.message
              : "Не удалось загрузить кабинет модератора",
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

  const updateNote = (key: string, value: string) => {
    setNotes((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const handleVacancyModeration = async (
    vacancy: Vacancy,
    action: "approve" | "reject",
  ) => {
    const key = `vacancy_${vacancy.id}`;

    try {
      setProcessingKey(`${key}_${action}`);
      setError("");
      setSuccess("");

      await moderateVacancy(vacancy.id, action, notes[key] || "");

      setPendingVacancies((current) =>
        current.filter((item) => item.id !== vacancy.id),
      );

      setSuccess(
        action === "approve"
          ? `Вакансия #${vacancy.id} одобрена`
          : `Вакансия #${vacancy.id} отклонена`,
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось промодерировать вакансию",
      );
    } finally {
      setProcessingKey("");
    }
  };

  const handleApplicationModeration = async (
    application: ApplicationListItem,
    action: "finish" | "reject",
  ) => {
    const key = `application_${application.id}`;

    try {
      setProcessingKey(`${key}_${action}`);
      setError("");
      setSuccess("");

      await moderateApplication(application.id, {
        action,
        moderator_note: notes[key] || "",
      });

      setFormedApplications((current) =>
        current.filter((item) => item.id !== application.id),
      );

      setSuccess(
        action === "finish"
          ? `Заявка #${application.id} завершена`
          : `Заявка #${application.id} отклонена`,
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось обработать заявку",
      );
    } finally {
      setProcessingKey("");
    }
  };

  return (
    <>
      <section className="hero-card">
        <div>
          <span className="eyebrow">Кабинет модератора</span>
          <h1 className="page-title">Модерация вакансий и завершение заявок</h1>
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
          <h2>Вакансии на модерации</h2>

          <div className="moderation-stack">
            {pendingVacancies.length > 0 ? (
              pendingVacancies.map((vacancy) => {
                const key = `vacancy_${vacancy.id}`;

                return (
                  <div className="moderation-card" key={vacancy.id}>
                    <div>
                      <strong>{vacancy.title}</strong>
                      <div>
                        {vacancy.company} • {vacancy.city}
                      </div>
                      <div className="muted">
                        Автор: {vacancy.creator_login || "—"}
                      </div>
                    </div>

                    <div className="moderation-form">
                      <textarea
                        rows={3}
                        placeholder="Комментарий модератора"
                        value={notes[key] || ""}
                        onChange={(event) => updateNote(key, event.target.value)}
                      />

                      <div className="action-row">
                        <button
                          className="btn"
                          type="button"
                          disabled={!!processingKey}
                          onClick={() =>
                            handleVacancyModeration(vacancy, "approve")
                          }
                        >
                          {processingKey === `${key}_approve`
                            ? "Одобрение..."
                            : "Одобрить"}
                        </button>

                        <button
                          className="btn btn-danger"
                          type="button"
                          disabled={!!processingKey}
                          onClick={() =>
                            handleVacancyModeration(vacancy, "reject")
                          }
                        >
                          {processingKey === `${key}_reject`
                            ? "Отклонение..."
                            : "Отклонить"}
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="list-card list-card--static">
                <strong>Нет вакансий на модерации</strong>
              </div>
            )}
          </div>
        </section>

        <section className="glass-card">
          <h2>Сформированные заявки</h2>

          <div className="moderation-stack">
            {formedApplications.length > 0 ? (
              formedApplications.map((application) => {
                const key = `application_${application.id}`;

                return (
                  <div className="moderation-card" key={application.id}>
                    <div>
                      <strong>Заявка №{application.id}</strong>
                      <div>
                        Соискатель:{" "}
                        {application.applicant_name ||
                          application.creator_login ||
                          "—"}
                      </div>
                      <div className="muted">
                        Статус:{" "}
                        {APPLICATION_STATUS_LABELS[application.status]}
                      </div>
                    </div>

                    <div className="moderation-form">
                      <textarea
                        rows={3}
                        placeholder="Комментарий модератора"
                        value={notes[key] || ""}
                        onChange={(event) => updateNote(key, event.target.value)}
                      />

                      <div className="action-row">
                        <button
                          className="btn"
                          type="button"
                          disabled={!!processingKey}
                          onClick={() =>
                            handleApplicationModeration(application, "finish")
                          }
                        >
                          {processingKey === `${key}_finish`
                            ? "Завершение..."
                            : "Завершить"}
                        </button>

                        <button
                          className="btn btn-danger"
                          type="button"
                          disabled={!!processingKey}
                          onClick={() =>
                            handleApplicationModeration(application, "reject")
                          }
                        >
                          {processingKey === `${key}_reject`
                            ? "Отклонение..."
                            : "Отклонить"}
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="list-card list-card--static">
                <strong>Нет сформированных заявок</strong>
              </div>
            )}
          </div>
        </section>
      </div>
    </>
  );
};
