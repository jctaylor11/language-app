import { useQuery } from "@tanstack/react-query";

import { getSessionLog } from "../../api";

export default function SessionLog() {
  const sessionLog = useQuery({
    queryKey: ["sessionLog"],
    queryFn: () => getSessionLog(),
  });

  if (sessionLog.isPending) {
    return <p>Loading...</p>;
  }

  if (sessionLog.isError) {
    return <p>Error: {sessionLog.error.message}</p>;
  }

  return (
    <div>
      {sessionLog.data.map((row) => (
        <div key={row.session_id}>
          {row.session_id}
          {row.started_at}
          {row.session_type}
          {row.total_reviewed}
        </div>
      ))}
    </div>
  );
}
