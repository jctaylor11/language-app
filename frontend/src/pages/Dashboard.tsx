import { useQuery } from "@tanstack/react-query";

import { getWordEntries } from "../api";
import { DEV_USER_ID } from "../config";

export default function Dashboard() {
  const { data: wordEntries } = useQuery({
    queryKey: ["words_table"],
    queryFn: () => getWordEntries(DEV_USER_ID),
  });

  if (!wordEntries) {
    return <p>Loading...</p>;
  }

  return (
    <div className="border border-neutral-200 shadow-sm rounded-2xl overflow-hidden">
      <table className="w-full text-sm">
        <thead className="border-b border-neutral-200">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Target
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Source
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Times Reviewed
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Average time
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Accuracy
            </th>
          </tr>
        </thead>
        <tbody>
          {wordEntries.map((entry) => (
            <tr key={entry.id}>
              <td className="px-6 py-2 text-xs border-b border-neutral-200">
                {entry.target}
              </td>
              <td className="px-6 py-2 text-xs border-b border-neutral-200">
                {entry.source}
              </td>
              <td className="px-6 py-2 font-mono text-right text-xs border-b border-neutral-200">
                {entry.times_reviewed}
              </td>
              <td className="px-6 py-2 font-mono text-right text-xs border-b border-neutral-200">
                {entry.av_s_per_syllable.toFixed(2) ?? "-"}
              </td>
              <td className="px-6 py-2 font-mono text-right text-xs border-b border-neutral-200">
                {(entry.accuracy * 100).toFixed(0)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
