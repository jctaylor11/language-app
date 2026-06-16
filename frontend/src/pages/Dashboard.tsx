import { useQuery } from "@tanstack/react-query";

import { getWordEntries } from "../api";
import { DEV_USER_ID } from "../config";
import WordTable from "../components/WordTable";

export default function Dashboard() {
  const { data: wordEntries } = useQuery({
    queryKey: ["words_table"],
    queryFn: () => getWordEntries(DEV_USER_ID),
  });

  if (!wordEntries) {
    return <p>Loading...</p>;
  }

  return <WordTable wordEntries={wordEntries} />;
}
