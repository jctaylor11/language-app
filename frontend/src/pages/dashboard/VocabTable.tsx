import { useQuery } from "@tanstack/react-query";

import { getWordEntries } from "../../api";
import WordTable from "../../components/WordTable";

export default function VocabTable() {
  const { data: wordEntries } = useQuery({
    queryKey: ["words_table"],
    queryFn: () => getWordEntries(),
  });

  if (!wordEntries) {
    return <p>Loading...</p>;
  }

  return <WordTable wordEntries={wordEntries} />;
}
