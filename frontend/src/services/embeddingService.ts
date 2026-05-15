import { pipeline } from "@huggingface/transformers";
import type { Vacancy } from "../types/vacancy";

type FeatureExtractor = (
  text: string,
  options: {
    pooling: "mean";
    normalize: boolean;
  },
) => Promise<{
  data: Float32Array | number[];
}>;

export interface SimilarVacancyResult {
  vacancy: Vacancy;
  score: number;
}

let extractorPromise: Promise<FeatureExtractor> | null = null;

const getExtractor = async (): Promise<FeatureExtractor> => {
  if (!extractorPromise) {
    extractorPromise = pipeline(
      "feature-extraction",
      "Xenova/all-MiniLM-L6-v2",
    ) as unknown as Promise<FeatureExtractor>;
  }

  return extractorPromise;
};

const buildVacancyText = (vacancy: Vacancy): string => {
  return [
    vacancy.title,
    vacancy.company,
    vacancy.city,
    vacancy.schedule,
    vacancy.disability_support,
    vacancy.description,
  ]
    .filter(Boolean)
    .join(". ");
};

export const getTextEmbedding = async (text: string): Promise<number[]> => {
  const extractor = await getExtractor();

  const output = await extractor(text || " ", {
    pooling: "mean",
    normalize: true,
  });

  return Array.from(output.data);
};

export const cosineSimilarity = (
  firstVector: number[],
  secondVector: number[],
): number => {
  let dotProduct = 0;
  let firstLength = 0;
  let secondLength = 0;

  const length = Math.min(firstVector.length, secondVector.length);

  for (let index = 0; index < length; index += 1) {
    const firstValue = firstVector[index];
    const secondValue = secondVector[index];

    dotProduct += firstValue * secondValue;
    firstLength += firstValue * firstValue;
    secondLength += secondValue * secondValue;
  }

  if (firstLength === 0 || secondLength === 0) {
    return 0;
  }

  return dotProduct / (Math.sqrt(firstLength) * Math.sqrt(secondLength));
};

export const findSimilarVacancies = async (
  currentVacancy: Vacancy,
  vacancies: Vacancy[],
  limit = 3,
): Promise<SimilarVacancyResult[]> => {
  const currentText = buildVacancyText(currentVacancy);
  const currentEmbedding = await getTextEmbedding(currentText);

  const candidates = vacancies.filter(
    (vacancy) => vacancy.id !== currentVacancy.id,
  );

  const results = await Promise.all(
    candidates.map(async (vacancy) => {
      const candidateText = buildVacancyText(vacancy);
      const candidateEmbedding = await getTextEmbedding(candidateText);

      return {
        vacancy,
        score: cosineSimilarity(currentEmbedding, candidateEmbedding),
      };
    }),
  );

  return results
    .sort((first, second) => second.score - first.score)
    .slice(0, limit);
};
