import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, XAxis } from "recharts";
import { getReviewChartData } from "../api";

export default function ReviewsChart() {
  const reviewChartData = useQuery({
    queryKey: ["reviewChartData"],
    queryFn: () => getReviewChartData(),
  });

  if (reviewChartData.isPending) {
    return <p>Loading...</p>;
  }

  if (reviewChartData.isError) {
    return <p>Error: {reviewChartData.error.message}</p>;
  }

  return (
    <BarChart
      style={{ width: "100%", aspectRatio: 3, maxWidth: 1000 }}
      data={reviewChartData.data}
    >
      <Bar dataKey="reviews" />
      <XAxis dataKey="series_date" />
    </BarChart>
  );
}
