import { Link } from "react-router-dom";
import { ROUTES } from "../routes";

export interface BreadcrumbItem {
  label: string;
  path?: string;
}

interface AppBreadcrumbsProps {
  items: BreadcrumbItem[];
}

export const AppBreadcrumbs = ({ items }: AppBreadcrumbsProps) => {
  return (
    <div className="breadcrumbs">
      <Link to={ROUTES.VACANCIES}>Главная</Link>

      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <span key={`${item.label}-${index}`}>
            {" / "}

            {isLast || !item.path ? (
              <span>{item.label}</span>
            ) : (
              <Link to={item.path}>{item.label}</Link>
            )}
          </span>
        );
      })}
    </div>
  );
};
