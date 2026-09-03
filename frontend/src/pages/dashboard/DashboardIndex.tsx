import { useQuery } from "@tanstack/react-query";
import type { DashboardHeroMetrics } from "../../types";
import { getHeroMetrics } from "../../api";
import WordsChart from "../../components/WordChart";
import ReviewsChart from "../../components/ReviewsChart";

const KPI_CONFIG = {
  total_words: { label: "Total Words", format: (v: number) => v },
  words_reviewed: { label: "Total reviewed", format: (v: number) => v },
};

export default function DashboardIndex() {
  const heroMetrics = useQuery({
    queryKey: ["heroMetrics"],
    queryFn: () => getHeroMetrics(),
  });

  if (heroMetrics.isPending) {
    return <p>Loading...</p>;
  }

  if (heroMetrics.isError) {
    return <p>Error: {heroMetrics.error.message}</p>;
  }

  return (
    <div className="h-full flex flex-col gap-4 overflow-hidden">
      <div className="grid grid-cols-2 gap-2 shrink-0">
        {Object.entries(KPI_CONFIG).map(([key, config]) => (
          <div
            key={config.label}
            className="flex flex-col border border-neutral-200 rounded p-4"
          >
            <span className="text-xs text-neutral-500 uppercase">
              {config.label}
            </span>
            <span className="text-xl font-mono mt-2">
              {config.format(
                heroMetrics.data[key as keyof DashboardHeroMetrics],
              )}
            </span>
          </div>
        ))}
      </div>
      <div className="flex-1 min-h-0 flex flex-col gap-4">
        <div className="flex-1 min-h-0">
          <ReviewsChart />
        </div>
        <div className="flex-1 min-h-0">
          <WordsChart />
        </div>
      </div>
    </div>
  );
}
