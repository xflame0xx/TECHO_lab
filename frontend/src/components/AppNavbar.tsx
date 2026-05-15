import { Link, useNavigate } from "react-router-dom";
import { ROUTES } from "../routes";
import type { CurrentUser } from "../types/auth";
import { ROLE_LABELS } from "../types/auth";

interface AppNavbarProps {
  user: CurrentUser | null;
  onLogout: () => Promise<void>;
}

export const AppNavbar = ({ user, onLogout }: AppNavbarProps) => {
  const navigate = useNavigate();

  const handleLogout = async () => {
    await onLogout();
    navigate(ROUTES.LOGIN);
  };

  return (
    <header className="topbar">
      <Link to={ROUTES.VACANCIES} className="brand">
        <span className="brand-badge">JA</span>

        <span className="brand-text">
          <strong className="brand-name">JobAbility</strong>
          <small className="brand-sub">Платформа вакансий и откликов</small>
        </span>
      </Link>

      <nav className="topnav">
        <Link to={ROUTES.VACANCIES}>Вакансии</Link>

        {user && (user.role === "applicant" || user.role === "moderator") && (
          <Link to={ROUTES.APPLICATIONS}>Заявки</Link>
        )}

        {user?.role === "applicant" && (
          <Link to={ROUTES.APPLICANT_CABINET}>Личный кабинет</Link>
        )}

        {user?.role === "employer" && (
          <>
            <Link to={ROUTES.EMPLOYER_CABINET}>Личный кабинет</Link>
            <Link to={ROUTES.EMPLOYER_RESPONSES}>Отклики</Link>
          </>
        )}

        {user?.role === "moderator" && (
          <Link to={ROUTES.MODERATOR_CABINET}>Личный кабинет</Link>
        )}

        <a href={ROUTES.SWAGGER}>Swagger</a>
        <a href={ROUTES.ADMIN}>Admin</a>
      </nav>

      <div className="userbox">
        {user ? (
          <>
            <div className="user-meta">
              <div className="user-name">{user.full_name || user.username}</div>
              <div className="user-role">{ROLE_LABELS[user.role]}</div>
            </div>

            <button type="button" className="btn btn-ghost" onClick={handleLogout}>
              Выйти
            </button>
          </>
        ) : (
          <>
            <Link to={ROUTES.LOGIN} className="btn btn-ghost">
              Войти
            </Link>

            <Link to={ROUTES.REGISTER} className="btn">
              Регистрация
            </Link>
          </>
        )}
      </div>
    </header>
  );
};
