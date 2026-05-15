import type { ReactElement } from "react";
import { Navigate } from "react-router-dom";
import { ROUTES } from "../routes";
import type { CurrentUser, UserRole } from "../types/auth";

interface ProtectedRouteProps {
  user: CurrentUser | null;
  roles?: UserRole[];
  children: ReactElement;
}

export const ProtectedRoute = ({
  user,
  roles,
  children,
}: ProtectedRouteProps) => {
  if (!user) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  if (roles && !roles.includes(user.role)) {
    return <Navigate to={ROUTES.VACANCIES} replace />;
  }

  return children;
};
