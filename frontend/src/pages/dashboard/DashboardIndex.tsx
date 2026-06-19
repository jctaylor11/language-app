import { useQuery } from "@tanstack/react-query";
import type { DashboardHeroMetrics } from "../../types";
import { getHeroMetrics } from "../../api";
import { DEV_USER_ID } from "../../config";

const KPI_CONFIG = {
  total_words: { label: "Total Words", format: (v: number) => v },
  words_reviewed: { label: "Total reviewed", format: (v: number) => v },
  accuracy: {
    label: "Accuracy",
    format: (v: number) => `${(v * 100).toFixed(0)}%`,
  },
};

export default function DashboardIndex() {
  const heroMetrics = useQuery({
    queryKey: ["heroMetrics"],
    queryFn: () => getHeroMetrics(DEV_USER_ID),
  });

  if (heroMetrics.isPending) {
    return <p>Loading...</p>;
  }

  if (heroMetrics.isError) {
    return <p>Error: {heroMetrics.error.message}</p>;
  }

  return (
    <div className="grid grid-cols-3 gap-2">
      {Object.entries(KPI_CONFIG).map(([key, config]) => (
        <div
          key={config.label}
          className="flex flex-col border border-neutral-200 rounded p-4"
        >
          <span className="text-xs text-neutral-500 uppercase">
            {config.label}
          </span>
          <span className="text-xl font-mono mt-2">
            {config.format(heroMetrics.data[key as keyof DashboardHeroMetrics])}
          </span>
        </div>
      ))}
    </div>
  );
}
