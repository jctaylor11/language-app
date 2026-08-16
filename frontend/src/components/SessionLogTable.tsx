import type { SessionLogEntry } from "../types";

import { formatSessionDate } from "../utils";

type Props = {
  sessionLogEntries: SessionLogEntry[];
};

export default function SessionLogTable({ sessionLogEntries }: Props) {
  if (!sessionLogEntries.length) {
    return <p className="text-sm text-neutral-400">No sessions yet</p>;
  }
  return (
    <div className="overflow-hidden">
      <table className="w-full text-sm">
        <thead className="border-b border-neutral-200">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Date
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Type
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Total Reviewed
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Session Link
            </th>
          </tr>
        </thead>
        <tbody>
          {sessionLogEntries.map((entry) => (
            <tr key={entry.session_id}>
              <td className="px-6 py-2 text-xs border-b border-neutral-200">
                {formatSessionDate(entry.started_at)}
              </td>
              <td className="px-6 py-2 text-xs border-b border-neutral-200 capitalize">
                {entry.session_type}
              </td>
              <td className="px-6 py-2 text-xs border-b border-neutral-200 capitalize">
                {entry.total_reviewed}
              </td>
              <td className="px-6 py-2 text-xs border-b border-neutral-200">
                [link]{entry.session_type === "vocab" ? "Words" : "Sentences"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
