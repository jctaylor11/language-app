import { Fragment } from "react";
import { useNavigate, useParams } from "react-router";

import type { SessionLogEntry } from "../types";
import { formatSessionDate } from "../utils";

type Props = {
  sessionLogEntries: SessionLogEntry[];
};

export default function SessionLogTable({ sessionLogEntries }: Props) {
  const { sessionId } = useParams(); // To pull the session ID return from the toggleSession navigation
  const expandedSessionId = Number(sessionId); // NaN when no session is in the URL so none expanded
  const navigate = useNavigate();

  function toggleSession(clickedSessionId: number) {
    if (clickedSessionId === expandedSessionId) {
      navigate("/dashboard/session-log"); // To collapse the summary if the same one is clicked again
      return;
    }
    navigate(`/dashboard/session-log/${clickedSessionId}`);
  }

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
          {sessionLogEntries.map((entry) => {
            const isExpanded = entry.session_id === expandedSessionId;

            return (
              // Fragment as each row needs a prop, for key for identification for expansion
              <Fragment key={entry.session_id}>
                <tr>
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
                    <button
                      onClick={() => toggleSession(entry.session_id)}
                      className="underline cursor-pointer"
                    >
                      {entry.session_type === "vocab" ? "Words" : "Sentences"}
                    </button>
                  </td>
                </tr>
                {isExpanded && (
                  <tr>
                    <td
                      colSpan={4}
                      className="px-6 py-3 text-xs bg-neutral-50 border-b border-neutral-200"
                    >
                      Placeholder: session {entry.session_id} summary
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
