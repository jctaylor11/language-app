import { useQuery } from "@tanstack/react-query";

import { getHeroMetrics } from "../../../api";

type HeroMetricsUIProps = {
  totalWords: number;
  wordsReviewed: number;
};

export default function HeroMetrics() {
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
    <HeroMetricsUI
      totalWords={heroMetrics.data.total_words}
      wordsReviewed={heroMetrics.data.words_reviewed}
    />
  );
}

function HeroMetricsUI({ totalWords, wordsReviewed }: HeroMetricsUIProps) {
  const tiles = [
    { label: "Total Words", value: totalWords },
    { label: "Total reviewed", value: wordsReviewed },
  ];

  return (
    <div className="grid grid-cols-2 gap-2">
      {tiles.map(({ label, value }) => (
        <div
          key={label}
          className="flex flex-col border border-neutral-200 rounded p-4"
        >
          <span className="text-xs text-neutral-500 uppercase">{label}</span>
          <span className="text-xl font-mono mt-2">{value}</span>
        </div>
      ))}
    </div>
  );
}
