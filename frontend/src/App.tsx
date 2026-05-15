import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { getCurrentUser, logoutUser } from "./api/authApi";

import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";

import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { VacanciesPage } from "./pages/VacanciesPage";
import { VacancyDetailPage } from "./pages/VacancyDetailPage";
import { ApplicationsPage } from "./pages/ApplicationsPage";
import { ApplicationDetailPage } from "./pages/ApplicationDetailPage";
import { ApplicantCabinetPage } from "./pages/ApplicantCabinetPage";
import { EmployerCabinetPage } from "./pages/EmployerCabinetPage";
import { EmployerResponsesPage } from "./pages/EmployerResponsesPage";
import { ModeratorCabinetPage } from "./pages/ModeratorCabinetPage";

import { ROUTES } from "./routes";
import type { CurrentUser } from "./types/auth";

const App = () => {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [userLoading, setUserLoading] = useState(true);

  useEffect(() => {
    const loadUser = async () => {
      const currentUser = await getCurrentUser();

      setUser(currentUser);
      setUserLoading(false);
    };

    loadUser();
  }, []);

  const handleLogout = async () => {
    await logoutUser();
    setUser(null);
  };

  if (userLoading) {
    return <main className="page">Загрузка пользователя...</main>;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout user={user} onLogout={handleLogout} />}>
          <Route
            path={ROUTES.HOME}
            element={<Navigate to={ROUTES.VACANCIES} replace />}
          />

          <Route
            path="/static/frontend/"
            element={<Navigate to={ROUTES.VACANCIES} replace />}
          />

          <Route
            path={ROUTES.LOGIN}
            element={<LoginPage onLogin={setUser} />}
          />

          <Route
            path={ROUTES.REGISTER}
            element={<RegisterPage />}
          />

          <Route
            path={ROUTES.VACANCIES}
            element={<VacanciesPage user={user} />}
          />

          <Route
            path={ROUTES.VACANCY_DETAIL}
            element={<VacancyDetailPage user={user} />}
          />

          <Route
            path={ROUTES.APPLICATIONS}
            element={
              <ProtectedRoute user={user} roles={["applicant", "moderator"]}>
                <ApplicationsPage user={user} />
              </ProtectedRoute>
            }
          />

          <Route
            path={ROUTES.APPLICATION_DETAIL}
            element={
              <ProtectedRoute user={user} roles={["applicant", "moderator"]}>
                <ApplicationDetailPage user={user} />
              </ProtectedRoute>
            }
          />

          <Route
            path={ROUTES.APPLICANT_CABINET}
            element={
              <ProtectedRoute user={user} roles={["applicant"]}>
                <ApplicantCabinetPage user={user!} />
              </ProtectedRoute>
            }
          />

          <Route
            path={ROUTES.EMPLOYER_CABINET}
            element={
              <ProtectedRoute user={user} roles={["employer"]}>
                <EmployerCabinetPage user={user!} />
              </ProtectedRoute>
            }
          />

          <Route
            path={ROUTES.EMPLOYER_RESPONSES}
            element={
              <ProtectedRoute user={user} roles={["employer"]}>
                <EmployerResponsesPage user={user!} />
              </ProtectedRoute>
            }
          />

          <Route
            path={ROUTES.MODERATOR_CABINET}
            element={
              <ProtectedRoute user={user} roles={["moderator"]}>
                <ModeratorCabinetPage user={user!} />
              </ProtectedRoute>
            }
          />

          <Route
            path="*"
            element={<Navigate to={ROUTES.VACANCIES} replace />}
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
