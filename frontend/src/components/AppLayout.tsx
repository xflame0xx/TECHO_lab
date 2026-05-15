import { Outlet } from "react-router-dom";
import { AppNavbar } from "./AppNavbar";
import type { CurrentUser } from "../types/auth";

interface AppLayoutProps {
  user: CurrentUser | null;
  onLogout: () => Promise<void>;
}

export const AppLayout = ({ user, onLogout }: AppLayoutProps) => {
  return (
    <>
      <AppNavbar user={user} onLogout={onLogout} />

      <main className="page">
        <Outlet />
      </main>
    </>
  );
};
