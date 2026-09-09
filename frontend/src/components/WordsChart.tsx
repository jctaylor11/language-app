import { useQuery } from "@tanstack/react-query";
import { Line, LineChart, ResponsiveContainer, XAxis, Tooltip } from "recharts";

import type { WordChartDataPoint } from "../types";
import { getWordChartData } from "../api";
import { formatSessionDate } from "../utils";

type WordsChartUIProps = {
  dataPoints: WordChartDataPoint[];
};

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

  return <WordsChartUI dataPoints={wordChartData.data} />;
}

function WordsChartUI({ dataPoints }: WordsChartUIProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={dataPoints}>
        <Line
          dataKey="cum_words"
          name="Total words"
          dot={false}
          activeDot={{ r: 4 }}
        />
        <XAxis dataKey="series_date" tickFormatter={formatSessionDate} />
        <Tooltip
          labelFormatter={(label) => formatSessionDate(String(label))}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
