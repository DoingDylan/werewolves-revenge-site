// src/data/classes.ts
//
// Single source of truth for role "class" colors (Investigation,
// Elimination, Manipulation, Protection, etc). Mirrors src/data/factions.ts —
// each class maps to a plain hex code, applied via a `--class` CSS custom
// property (see global.css for the rules that consume it) so any hex code
// works without needing a matching Tailwind utility class.

export interface ClassTheme {
  /** Display name shown in the UI. */
  label: string;
  /** Hex color for this class, e.g. "#3b82f6". */
  hex: string;
}

const DEFAULT_THEME: ClassTheme = {
  label: 'Unknown',
  hex: '#71717a', // zinc-500
};

export const CLASS_THEMES: Record<string, ClassTheme> = {
  Investigation: { label: 'Investigation', hex: '#B38FC4' },
  Elimination: { label: 'Elimination', hex: '#883532' },
  Manipulation: { label: 'Manipulation', hex: '#839C38' },
  Protection: { label: 'Protection', hex: '#5F90C4' },
};

/** Looks up a class's theme, falling back to a neutral zinc theme for unknown classes. */
export function getClassTheme(roleClass?: string | null): ClassTheme {
  return (roleClass && CLASS_THEMES[roleClass]) || DEFAULT_THEME;
}
