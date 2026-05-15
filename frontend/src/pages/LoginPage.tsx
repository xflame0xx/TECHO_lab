import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Alert, Spinner } from "react-bootstrap";
import { loginUser } from "../api/authApi";
import { ROUTES } from "../routes";
import type { CurrentUser, LoginPayload } from "../types/auth";

interface LoginPageProps {
  onLogin: (user: CurrentUser) => void;
}

const DEMO_MODERATOR = {
  username: "Ilya Snytkin",
  password: "Ilya123",
};

export const LoginPage = ({ onLogin }: LoginPageProps) => {
  const navigate = useNavigate();

  const [form, setForm] = useState<LoginPayload>({
    username: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const updateField = (field: keyof LoginPayload, value: string) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const fillModerator = () => {
    setForm({
      username: DEMO_MODERATOR.username,
      password: DEMO_MODERATOR.password,
    });
  };

  const redirectByRole = (user: CurrentUser) => {
    if (user.role === "applicant") {
      navigate(ROUTES.APPLICANT_CABINET);
      return;
    }

    if (user.role === "employer") {
      navigate(ROUTES.EMPLOYER_CABINET);
      return;
    }

    navigate(ROUTES.MODERATOR_CABINET);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    try {
      setLoading(true);
      setError("");

      const user = await loginUser(form);

      onLogin(user);
      redirectByRole(user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="ja-auth-screen">
      <div className="ja-auth-info">
        <span className="ja-section-label">Авторизация</span>

        <h1>Вход в систему</h1>

        <p>
          Введите логин и пароль. Роль пользователя определяется автоматически
          после успешной авторизации на backend.
        </p>

        <div className="ja-demo-box">
          <div className="ja-demo-box__title">Быстрое заполнение</div>

          <div className="ja-demo-box__row">
            <span>Логин</span>
            <strong>{DEMO_MODERATOR.username}</strong>
          </div>

          <div className="ja-demo-box__row">
            <span>Пароль</span>
            <strong>{DEMO_MODERATOR.password}</strong>
          </div>

          <button
            type="button"
            className="ja-button ja-button--light"
            onClick={fillModerator}
          >
            Подставить Илью Сныткина
          </button>
        </div>

        <div className="ja-hint-box">
          В mock-режиме также можно использовать логины:{" "}
          <b>applicant</b>, <b>employer</b>, <b>moderator</b>.
        </div>
      </div>

      <form className="ja-auth-form" onSubmit={handleSubmit}>
        <h2>Войти</h2>

        {error && <Alert variant="danger">{error}</Alert>}

        <label className="ja-form-field">
          <span>Логин</span>
          <input
            value={form.username}
            required
            autoComplete="username"
            onChange={(event) => updateField("username", event.target.value)}
          />
        </label>

        <label className="ja-form-field">
          <span>Пароль</span>
          <input
            type="password"
            value={form.password}
            required
            autoComplete="current-password"
            onChange={(event) => updateField("password", event.target.value)}
          />
        </label>

        <button
          className="ja-button ja-button--wide"
          type="submit"
          disabled={loading}
        >
          {loading ? <Spinner size="sm" animation="border" /> : "Войти"}
        </button>
      </form>
    </section>
  );
};
