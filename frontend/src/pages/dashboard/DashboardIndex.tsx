const KPI_CONFIG = {
  total_words: { label: "Total Words", format: (v: number) => v },
  words_reviewed: { label: "Total reviewed", format: (v: number) => v },
  accuracy: {
    label: "Accuracy",
    format: (v: number) => `${(v * 100).toFixed(0)}%`,
  },
};

type DashboardHeroMetrics = {
  total_words: number;
  words_reviewed: number;
  accuracy: number;
};

export default function DashboardIndex() {
  // Mock data that will be from useQuery once wired up
  const mock: DashboardHeroMetrics = {
    total_words: 50,
    words_reviewed: 200,
    accuracy: 0.9,
  };

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
            {config.format(mock[key as keyof DashboardHeroMetrics])}
          </span>
        </div>
      ))}
    </div>
  );
}
