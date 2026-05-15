import { useEffect, useState } from "react";
import type { ApplicationLine } from "../types/application";

interface ApplicationLineCardProps {
  line: ApplicationLine;
  editable: boolean;
  saving: boolean;
  onSave: (line: ApplicationLine, qty: number, comment: string) => Promise<void>;
  onDelete: (line: ApplicationLine) => Promise<void>;
}

const FALLBACK_IMAGE = "/fallback.svg";

export const ApplicationLineCard = ({
  line,
  editable,
  saving,
  onSave,
  onDelete,
}: ApplicationLineCardProps) => {
  const [qty, setQty] = useState(line.qty);
  const [comment, setComment] = useState(line.comment || "");

  useEffect(() => {
    setQty(line.qty);
    setComment(line.comment || "");
  }, [line.id, line.qty, line.comment]);

  const lineTotal = qty * line.vacancy.salary;

  return (
    <article className="ja-application-line-card">
      <div className="ja-application-line-card__image">
        <img
          src={line.vacancy.image_url || FALLBACK_IMAGE}
          alt={line.vacancy.title}
          onError={(event) => {
            event.currentTarget.src = FALLBACK_IMAGE;
          }}
        />
      </div>

      <div className="ja-application-line-card__content">
        <h3>{line.vacancy.title}</h3>

        <div className="ja-application-line-card__meta">
          {line.vacancy.company} • {line.vacancy.city}
        </div>

        <div className="ja-application-line-card__salary">
          Зарплата: <b>{line.vacancy.salary.toLocaleString("ru-RU")} ₽</b>
        </div>

        <div className="ja-application-line-card__salary">
          Сумма строки: <b>{lineTotal.toLocaleString("ru-RU")} ₽</b>
        </div>
      </div>

      <div className="ja-application-line-card__controls">
        <label className="ja-form-field">
          <span>Количество</span>
          <input
            type="number"
            min="1"
            disabled={!editable || saving}
            value={qty}
            onChange={(event) =>
              setQty(Math.max(1, Number(event.target.value) || 1))
            }
          />
        </label>

        <label className="ja-form-field">
          <span>Комментарий</span>
          <textarea
            rows={4}
            disabled={!editable || saving}
            placeholder="Комментарий к вакансии"
            value={comment}
            onChange={(event) => setComment(event.target.value)}
          />
        </label>

        {editable && (
          <div className="ja-application-line-card__actions">
            <button
              className="ja-button"
              type="button"
              disabled={saving}
              onClick={() => onSave(line, qty, comment)}
            >
              Сохранить
            </button>

            <button
              className="ja-button ja-button--danger"
              type="button"
              disabled={saving}
              onClick={() => onDelete(line)}
            >
              Удалить
            </button>
          </div>
        )}
      </div>
    </article>
  );
};
