import type { FormEvent } from "react";
import type { VacancyFilters as VacancyFiltersType } from "../types/vacancy";

interface VacancyFiltersProps {
  filters: VacancyFiltersType;
  loading: boolean;
  onChange: (filters: VacancyFiltersType) => void;
  onSubmit: () => void;
  onReset: () => void;
}

export const VacancyFilters = ({
  filters,
  loading,
  onChange,
  onSubmit,
  onReset,
}: VacancyFiltersProps) => {
  const updateField = (field: keyof VacancyFiltersType, value: string) => {
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
    <form className="search" onSubmit={handleSubmit}>
      <input
        type="text"
        value={filters.search}
        placeholder="Поиск: название / компания / город"
        autoComplete="off"
        onChange={(event) => updateField("search", event.target.value)}
      />

      <input
        type="number"
        min="0"
        value={filters.minPrice}
        placeholder="Цена от"
        onChange={(event) => updateField("minPrice", event.target.value)}
      />

      <input
        type="number"
        min="0"
        value={filters.maxPrice}
        placeholder="Цена до"
        onChange={(event) => updateField("maxPrice", event.target.value)}
      />

      <input
        type="date"
        value={filters.dateFrom}
        onChange={(event) => updateField("dateFrom", event.target.value)}
      />

      <input
        type="date"
        value={filters.dateTo}
        onChange={(event) => updateField("dateTo", event.target.value)}
      />

      <button type="submit" disabled={loading}>
        Найти
      </button>

      <button type="button" disabled={loading} onClick={onReset}>
        Сбросить
      </button>
    </form>
  );
};
