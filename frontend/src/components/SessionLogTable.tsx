import { Fragment } from "react";
import { useNavigate, useParams } from "react-router";
import { useQuery } from "@tanstack/react-query";

import type { SessionLogEntry } from "../types";
import { formatSessionDate } from "../utils";
import { getSessionOverview } from "../api";

type SessionLogTableProps = {
  sessionLogEntries: SessionLogEntry[];
};

type SessionOverviewProps = {
  sessionId: number;
};

function SessionOverview({ sessionId }: SessionOverviewProps) {
  const sessionOverview = useQuery({
    queryKey: ["sessionOverview", sessionId],
    queryFn: () => getSessionOverview(sessionId),
  });

  if (sessionOverview.isPending) {
    return <p>Loading...</p>;
  }

  if (sessionOverview.isError) {
    return <p>Error: {sessionOverview.error.message}</p>;
  }

  return (
    <ul className="grid grid-cols-4 gap-x-8">
      {sessionOverview.data.map((target, index) => (
        <li key={index} className="py-0.5">
          {target}
        </li>
      ))}
    </ul>
  );
}

export default function SessionLogTable({
  sessionLogEntries,
}: SessionLogTableProps) {
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
            <th className="w-12 pl-6 pr-2 py-3" /> {/* Index column, deliberately unlabelled */}
            <th className="w-48 px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Date
            </th>
            <th className="w-32 px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Type
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Total Reviewed
            </th>
          </tr>
        </thead>
        <tbody>
          {sessionLogEntries.map((entry) => {
            const isExpanded = entry.session_id === expandedSessionId;

            let rowClassName =
              "cursor-pointer transition-colors hover:bg-neutral-50";
            let cellBorderClassName = "border-b border-neutral-200";

            if (isExpanded) {
              rowClassName = "cursor-pointer bg-neutral-50";
              cellBorderClassName = "border-b border-transparent"; // Transparent rather than removed so the row keeps its height
            }

            const cellClassName = `px-6 py-2 text-xs ${cellBorderClassName}`;
            const indexCellClassName = `pl-6 pr-2 py-2 text-xs text-right font-mono text-neutral-400 ${cellBorderClassName}`;

            return (
              // Fragment as each row needs a prop, for key for identification for expansion
              <Fragment key={entry.session_id}>
                <tr
                  onClick={() => toggleSession(entry.session_id)}
                  className={rowClassName}
                >
                  <td className={indexCellClassName}>{entry.session_number}</td>
                  <td className={cellClassName}>
                    {formatSessionDate(entry.started_at)}
                  </td>
                  <td className={`${cellClassName} capitalize`}>
                    {entry.session_type}
                  </td>
                  <td className={`${cellClassName} font-mono text-right`}>
                    {entry.total_reviewed}
                  </td>
                </tr>
                {isExpanded && (
                  <tr>
                    <td className="bg-neutral-50 border-b border-neutral-200" />
                    <td
                      colSpan={3}
                      className="px-6 py-3 text-xs bg-neutral-50 border-b border-neutral-200"
                    >
                      <SessionOverview sessionId={entry.session_id} />
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
