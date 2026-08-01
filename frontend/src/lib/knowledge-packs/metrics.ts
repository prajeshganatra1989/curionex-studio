/** Local writing metrics — never invent values. */

export function countCharacters(text: string): number {
  return text.length;
}

export function countWords(text: string): number {
  const trimmed = text.trim();
  if (!trimmed) return 0;
  return trimmed.split(/\s+/).filter(Boolean).length;
}

/** Average adult reading pace for research notes. */
const WORDS_PER_MINUTE = 200;

export function estimatedReadingMinutes(wordCount: number): number {
  if (wordCount <= 0) return 0;
  return Math.max(1, Math.ceil(wordCount / WORDS_PER_MINUTE));
}

export function formatReadingTime(wordCount: number): string {
  if (wordCount <= 0) return "0 min";
  const minutes = estimatedReadingMinutes(wordCount);
  return minutes === 1 ? "1 min" : `${minutes} min`;
}

/** A section counts as complete when it has any non-whitespace content. */
export function isSectionComplete(content: string): boolean {
  return content.trim().length > 0;
}

export function completionPercent(contents: string[]): number {
  if (contents.length === 0) return 0;
  const done = contents.filter(isSectionComplete).length;
  return Math.round((done / contents.length) * 100);
}
