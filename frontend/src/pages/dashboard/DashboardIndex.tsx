import HeroMetrics from "../../components/HeroMetrics";
import WordsChart from "../../components/WordsChart";
import ReviewsChart from "../../components/ReviewsChart";

export default function DashboardIndex() {
  return (
    <div className="h-full flex flex-col gap-4 overflow-hidden">
      <div className="shrink-0">
        <HeroMetrics />
      </div>
      <div className="flex-1 min-h-0">
        <ReviewsChart />
      </div>
      <div className="flex-1 min-h-0">
        <WordsChart />
      </div>
    </div>
  );
}
