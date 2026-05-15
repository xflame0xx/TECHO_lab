import { Link } from "react-router-dom";
import type { ApplicationCart } from "../types/application";
import type { CurrentUser } from "../types/auth";

interface DraftApplicationCardProps {
  user: CurrentUser | null;
  cart: ApplicationCart | null;
}

export const DraftApplicationCard = ({ user, cart }: DraftApplicationCardProps) => {
  if (!user) {
    return (
      <div className="draft-empty">
        Войдите как соискатель, чтобы добавлять вакансии в заявку
      </div>
    );
  }

  if (user.role !== "applicant") {
    return (
      <div className="draft-empty">
        Текущая заявка доступна только для роли «Соискатель»
      </div>
    );
  }

  if (!cart || !cart.application_id) {
    return <div className="draft-empty">Текущей заявки нет</div>;
  }

  return (
    <div className="draft-card">
      <div className="draft-title">Текущая заявка</div>

      <div className="draft-row">
        ID: <b>{cart.application_id}</b>
      </div>

      <div className="draft-row">
        Кол-во позиций: <b>{cart.items_count}</b>
      </div>

      <Link className="draft-link" to={`/applications/${cart.application_id}`}>
        Открыть
      </Link>
    </div>
  );
};
