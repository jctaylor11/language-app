export function calcIncorrectInput(correctWord: string, allKeystrokes: string): string | null {
    if (allKeystrokes === correctWord) {
      return null
    }
    return allKeystrokes
  }
