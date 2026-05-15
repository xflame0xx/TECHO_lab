import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Alert, Spinner } from "react-bootstrap";
import { registerUser } from "../api/authApi";
import { ROUTES } from "../routes";
import type { RegisterPayload, UserRole } from "../types/auth";

export const RegisterPage = () => {
  const navigate = useNavigate();

  const [form, setForm] = useState<RegisterPayload>({
    first_name: "",
    last_name: "",
    username: "",
    email: "",
    password: "",
    role: "applicant",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const updateField = (field: keyof RegisterPayload, value: string) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const updateRole = (role: Exclude<UserRole, "moderator">) => {
    setForm((current) => ({
      ...current,
      role,
    }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    try {
      setLoading(true);
      setError("");

      await registerUser(form);

      navigate(ROUTES.LOGIN, {
        replace: true,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка регистрации");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-layout auth-layout--single">
      <div className="auth-hero">
        <span className="eyebrow">Регистрация</span>

        <h1>Создание аккаунта</h1>

        <p>
          После регистрации автоматический вход не выполняется. Для продолжения
          нужно вручную перейти на страницу входа и авторизоваться.
        </p>
      </div>

      <form className="auth-card" onSubmit={handleSubmit}>
        <h2>Новый аккаунт</h2>

        {error && <Alert variant="danger">{error}</Alert>}

        <div className="field-row">
          <div className="field">
            <label>Имя</label>
            <input
              value={form.first_name}
              onChange={(event) => updateField("first_name", event.target.value)}
            />
          </div>

          <div className="field">
            <label>Фамилия</label>
            <input
              value={form.last_name}
              onChange={(event) => updateField("last_name", event.target.value)}
            />
          </div>
        </div>

        <div className="field">
          <label>Username</label>
          <input
            value={form.username}
            required
            autoComplete="username"
            onChange={(event) => updateField("username", event.target.value)}
          />
        </div>

        <div className="field">
          <label>Email</label>
          <input
            type="email"
            value={form.email}
            autoComplete="email"
            onChange={(event) => updateField("email", event.target.value)}
          />
        </div>

        <div className="field">
          <label>Пароль</label>
          <input
            type="password"
            value={form.password}
            required
            autoComplete="new-password"
            onChange={(event) => updateField("password", event.target.value)}
          />
        </div>

        <div className="field">
          <label>Тип аккаунта</label>

          <div className="choice-grid choice-grid--two">
            <label className="choice-card">
              <input
                type="radio"
                name="role"
                value="employer"
                checked={form.role === "employer"}
                onChange={() => updateRole("employer")}
              />
              <span>Работодатель</span>
            </label>

            <label className="choice-card">
              <input
                type="radio"
                name="role"
                value="applicant"
                checked={form.role === "applicant"}
                onChange={() => updateRole("applicant")}
              />
              <span>Соискатель</span>
            </label>
          </div>
        </div>

        <button className="btn btn-block" type="submit" disabled={loading}>
          {loading ? <Spinner size="sm" animation="border" /> : "Создать аккаунт"}
        </button>
      </form>
    </section>
  );
};
