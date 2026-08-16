import { useQuery } from "@tanstack/react-query";

import { getSessionLog } from "../../api";
import SessionLogTable from "../../components/SessionLogTable";

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
      <SessionLogTable sessionLogEntries={sessionLog.data} />
    </div>
  );
}
