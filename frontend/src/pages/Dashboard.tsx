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
    <ul>
      {wordEntries.map((entry) => (
        <li key={entry.id}>
          {entry.target} - {entry.source} - {entry.times_reviewed} -{" "}
          {entry.av_s_per_syllable} - {entry.accuracy}
        </li>
      ))}
    </ul>
  );
}
