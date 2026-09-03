import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import { getReviewChartData } from "../api";
import { formatSessionDate } from "../utils";

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
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={reviewChartData.data}>
        <Bar dataKey="reviews" name="Reviews" />
        <XAxis dataKey="series_date" tickFormatter={formatSessionDate} />
        <Tooltip
          cursor={{ fill: "#00000010" }}
          labelFormatter={(label) => formatSessionDate(String(label))}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
