const TRAILING_TIMESTAMP_SUFFIX_REGEX = /\s+\d{8,}$/u;

export function normalizeProjectName(name: string | null | undefined): string {
  if (!name) {
    return "";
  }

  return name.replace(TRAILING_TIMESTAMP_SUFFIX_REGEX, "").trim();
}
