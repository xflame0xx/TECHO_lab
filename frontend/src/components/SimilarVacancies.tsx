import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchVacancies } from "../api/vacancyApi";
import {
  findSimilarVacancies,
  type SimilarVacancyResult,
} from "../services/embeddingService";

import {
  EMPTY_VACANCY_FILTERS,
  type Vacancy,
} from "../types/vacancy";

interface SimilarVacanciesProps {
  currentVacancy: Vacancy;
}

export const SimilarVacancies = ({
  currentVacancy,
}: SimilarVacanciesProps) => {
  const [items, setItems] = useState<SimilarVacancyResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;

    const loadSimilarVacancies = async () => {
      try {
        setLoading(true);
        setError("");

        const vacancies = await fetchVacancies(EMPTY_VACANCY_FILTERS);
        const similar = await findSimilarVacancies(currentVacancy, vacancies, 3);

        if (!ignore) {
          setItems(similar);
        }
      } catch (err) {
        if (!ignore) {
          setError(
            err instanceof Error
              ? err.message
              : "Не удалось рассчитать похожие вакансии",
          );
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    loadSimilarVacancies();

    return () => {
      ignore = true;
    };
  }, [currentVacancy]);

  return (
    <section className="similar-section">
      <h2>Похожие вакансии</h2>

      {loading && (
        <div className="similar-status">
          Загружается модель и рассчитываются эмбеддинги...
        </div>
      )}

      {error && !loading && (
        <div className="similar-status">
          Похожие вакансии временно недоступны: {error}
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <div className="similar-status">
          Похожих вакансий пока нет.
        </div>
      )}

      {!loading && !error && items.length > 0 && (
        <div className="similar-grid">
          {items.map(({ vacancy, score }) => (
            <article className="similar-card" key={vacancy.id}>
              <Link
                className="similar-card__title"
                to={`/vacancies/${vacancy.id}`}
              >
                {vacancy.title}
              </Link>

              <div className="similar-card__meta">
                {vacancy.company} • {vacancy.city}
              </div>

              <p className="similar-card__description">
                {vacancy.description}
              </p>

              <div className="similar-card__footer">
                <span>{vacancy.salary.toLocaleString("ru-RU")} ₽</span>
                <span>Похожесть: {Math.round(score * 100)}%</span>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
};
