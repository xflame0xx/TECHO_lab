import { Link, useNavigate } from "react-router-dom";

import { FALLBACK_IMAGE, setFallbackImage } from "../data/imageFallback";

import type { CurrentUser } from "../types/auth";
import type { Vacancy } from "../types/vacancy";

interface VacancyCardProps {
  vacancy: Vacancy;
  user: CurrentUser | null;
  adding: boolean;
  onAddToApplication: (vacancyId: number) => Promise<void>;
}

export const VacancyCard = ({
  vacancy,
  user,
  adding,
  onAddToApplication,
}: VacancyCardProps) => {
  const navigate = useNavigate();

  const handleAddClick = async () => {
    if (!user) {
      navigate("/login");
      return;
    }

    if (user.role !== "applicant") {
      return;
    }

    await onAddToApplication(vacancy.id);
  };

  return (
    <article className="ja-vacancy-card">
      <Link
        className="ja-vacancy-card__image-link"
        to={`/vacancies/${vacancy.id}`}
      >
        <div className="ja-vacancy-card__image-box">
          <img
            src={vacancy.image_url || FALLBACK_IMAGE}
            alt={vacancy.title}
            loading="lazy"
            decoding="async"
            onError={setFallbackImage}
          />
        </div>
      </Link>

      <div className="ja-vacancy-card__body">
        <Link
          className="ja-vacancy-card__title"
          to={`/vacancies/${vacancy.id}`}
        >
          {vacancy.title}
        </Link>

        <div className="ja-vacancy-card__meta">
          {vacancy.company} • {vacancy.city}
        </div>

        <div className="ja-vacancy-card__footer">
          <div className="ja-vacancy-card__salary">
            {vacancy.salary.toLocaleString("ru-RU")} ₽
          </div>

          <Link className="ja-button" to={`/vacancies/${vacancy.id}`}>
            Подробнее
          </Link>
        </div>

        <button
          className="ja-button ja-button--outline ja-button--wide"
          type="button"
          disabled={adding || (!!user && user.role !== "applicant")}
          onClick={handleAddClick}
        >
          {adding ? "Добавление..." : "В заявку"}
        </button>
      </div>
    </article>
  );
};
