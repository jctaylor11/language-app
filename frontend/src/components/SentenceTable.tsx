import { useQuery } from "@tanstack/react-query";

import type { SentenceEntry } from "../types";
import { getSentenceEntries } from "../api";

type SentenceTableUIProps = {
  sentenceEntries: SentenceEntry[];
};

export default function SentenceTable() {
  const sentenceEntriesQuery = useQuery({
    queryKey: ["sentenceEntries"],
    queryFn: () => getSentenceEntries(),
  });

  if (sentenceEntriesQuery.isPending) {
    return <p>Loading...</p>;
  }

  if (sentenceEntriesQuery.isError) {
    return <p>Error: {sentenceEntriesQuery.error.message}</p>;
  }

  return <SentenceTableUI sentenceEntries={sentenceEntriesQuery.data} />;
}

function SentenceTableUI({ sentenceEntries }: SentenceTableUIProps) {
  if (!sentenceEntries.length) {
    return <p className="text-sm text-neutral-400">No sentences yet</p>;
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
          </tr>
        </thead>
        <tbody>
          {sentenceEntries.map((entry) => (
            <tr key={entry.id}>
              <td className="px-6 py-2 text-xs border-b border-neutral-200">
                {entry.target}
              </td>
              <td className="px-6 py-2 text-xs border-b border-neutral-200">
                {entry.source}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
