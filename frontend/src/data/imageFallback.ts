import type { SyntheticEvent } from "react";

export const FALLBACK_IMAGE =
  "data:image/svg+xml;charset=UTF-8," +
  encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="360" height="220" viewBox="0 0 360 220">
      <rect width="360" height="220" rx="18" fill="#f2f4f7"/>
      <rect x="120" y="60" width="120" height="82" rx="14" fill="#ffffff"/>
      <circle cx="154" cy="91" r="13" fill="#d0d5dd"/>
      <path d="M132 132L163 106L183 123L202 104L228 132H132Z" fill="#d0d5dd"/>
      <text x="180" y="174" text-anchor="middle" font-family="Arial, sans-serif" font-size="15" fill="#667085">
        Нет изображения
      </text>
    </svg>
  `);

export const setFallbackImage = (
  event: SyntheticEvent<HTMLImageElement>,
) => {
  const image = event.currentTarget;

  image.onerror = null;
  image.src = FALLBACK_IMAGE;
};
