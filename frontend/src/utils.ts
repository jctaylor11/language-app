export function calcIncorrectInput(
  correctWord: string,
  allKeystrokes: string,
): string | null {
  if (allKeystrokes === correctWord) {
    return null;
  }
  return allKeystrokes;
}

export function formatSessionDate(isoTimestamp: string): string {
  const sessionDate = new Date(isoTimestamp);
  return sessionDate.toLocaleDateString("en-GB", {
    month: "short",
    day: "numeric",
  });
}
