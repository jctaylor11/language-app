import { useQuery } from "@tanstack/react-query";

import type { WordEntry } from "../types";
import { getWordEntries } from "../api";

type WordTableUIProps = {
  wordEntries: WordEntry[];
};

export default function WordTable() {
  const wordEntriesQuery = useQuery({
    queryKey: ["words_table"],
    queryFn: () => getWordEntries(),
  });

  if (wordEntriesQuery.isPending) {
    return <p>Loading...</p>;
  }

  if (wordEntriesQuery.isError) {
    return <p>Error: {wordEntriesQuery.error.message}</p>;
  }

  return <WordTableUI wordEntries={wordEntriesQuery.data} />;
}

function WordTableUI({ wordEntries }: WordTableUIProps) {
  if (!wordEntries.length) {
    return <p className="text-sm text-neutral-400">No words yet</p>;
  }
  return (
    <div className="overflow-hidden">
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
              Avg Time/Syllable
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
                {entry.av_s_per_syllable?.toFixed(2) ?? "-"}
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
