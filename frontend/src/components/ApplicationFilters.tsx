import type { FormEvent } from "react";
import {
  APPLICATION_STATUS_LABELS,
  type ApplicationFilters as ApplicationFiltersType,
  type ApplicationStatus,
} from "../types/application";

interface ApplicationFiltersProps {
  filters: ApplicationFiltersType;
  loading: boolean;
  onChange: (filters: ApplicationFiltersType) => void;
  onSubmit: () => void;
  onReset: () => void;
}

const STATUSES: ApplicationStatus[] = [
  "DRAFT",
  "FORMED",
  "FINISHED",
  "REJECTED",
  "DELETED",
];

export const ApplicationFilters = ({
  filters,
  loading,
  onChange,
  onSubmit,
  onReset,
}: ApplicationFiltersProps) => {
  const updateField = (field: keyof ApplicationFiltersType, value: string) => {
    onChange({
      ...filters,
      [field]: value,
    });
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit();
  };

  return (
    <form method="get" className="filters" autoComplete="off" onSubmit={handleSubmit}>
      <div className="f-group">
        <label>Статус</label>

        <select
          value={filters.status}
          onChange={(event) => updateField("status", event.target.value)}
        >
          <option value="">Любой статус</option>

          {STATUSES.map((status) => (
            <option value={status} key={status}>
              {APPLICATION_STATUS_LABELS[status]}
            </option>
          ))}
        </select>
      </div>

      <div className="f-group">
        <label>Дата начала</label>

        <input
          type="date"
          value={filters.dateFrom}
          onChange={(event) => updateField("dateFrom", event.target.value)}
        />
      </div>

      <div className="f-group">
        <label>Дата окончания</label>

        <input
          type="date"
          value={filters.dateTo}
          onChange={(event) => updateField("dateTo", event.target.value)}
        />
      </div>

      <div className="f-actions">
        <button className="btn" type="submit" disabled={loading}>
          Фильтр
        </button>

        <button
          className="btn btn-ghost"
          type="button"
          disabled={loading}
          onClick={onReset}
          style={{ marginLeft: 8 }}
        >
          Сбросить
        </button>
      </div>
    </form>
  );
};
