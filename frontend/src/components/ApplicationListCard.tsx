import { Link } from "react-router-dom";
import {
  APPLICATION_STATUS_LABELS,
  type ApplicationListItem,
} from "../types/application";

interface ApplicationListCardProps {
  application: ApplicationListItem;
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

export const ApplicationListCard = ({ application }: ApplicationListCardProps) => {
  const total = application.total_sum || application.total_salary || 0;

  return (
    <article className="ja-application-card">
      <div className="ja-application-card__main">
        <div className="ja-application-card__top">
          <Link
            className="ja-application-card__title"
            to={`/applications/${application.id}`}
          >
            Заявка №{application.id}
          </Link>

          <span
            className={`ja-status-badge ja-status-badge--${application.status.toLowerCase()}`}
          >
            {APPLICATION_STATUS_LABELS[application.status]}
          </span>
        </div>

        <div className="ja-application-card__grid">
          <div>
            <span>Создана</span>
            <strong>{formatDateTime(application.created_at)}</strong>
          </div>

          <div>
            <span>Сформирована</span>
            <strong>{formatDateTime(application.formed_at)}</strong>
          </div>

          <div>
            <span>Завершена</span>
            <strong>{formatDateTime(application.completed_at)}</strong>
          </div>

          <div>
            <span>Позиции</span>
            <strong>{application.lines_count || 0}</strong>
          </div>

          <div>
            <span>Сумма</span>
            <strong>{total.toLocaleString("ru-RU")} ₽</strong>
          </div>
        </div>
      </div>

      <div className="ja-application-card__actions">
        <Link
          className="ja-button ja-button--outline"
          to={`/applications/${application.id}`}
        >
          Открыть
        </Link>
      </div>
    </article>
  );
};
