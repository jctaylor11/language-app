import { useQuery } from "@tanstack/react-query";

import { getSentenceEntries } from "../../api";
import SentenceTable from "../../components/SentenceTable";

export default function SentenceVault() {
  const { data: sentenceEntries } = useQuery({
    queryKey: ["sentenceEntries"],
    queryFn: () => getSentenceEntries(),
  });

  if (!sentenceEntries) {
    return <p>Loading...</p>;
  }

  return <SentenceTable sentenceEntries={sentenceEntries} />;
}
