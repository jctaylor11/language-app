import { useQuery } from "@tanstack/react-query";
import { Line, LineChart, XAxis } from "recharts";
import { getWordChartData } from "../api";

export default function WordsChart() {
  const wordChartData = useQuery({
    queryKey: ["wordChartData"],
    queryFn: () => getWordChartData(),
  });

  if (wordChartData.isPending) {
    return <p>Loading...</p>;
  }

  if (wordChartData.isError) {
    return <p>Error: {wordChartData.error.message}</p>;
  }

  return (
    <LineChart
      style={{ width: "100%", aspectRatio: 3, maxWidth: 1000 }}
      data={wordChartData.data}
    >
      <Line dataKey="cum_words" />
      <XAxis dataKey="series_date" />
    </LineChart>
  );
}
