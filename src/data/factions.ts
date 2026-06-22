// src/data/factions.ts
//
// Single source of truth for faction colors. Each faction maps to a plain
// hex code, which gets passed into the page as a `--faction` CSS custom
// property (see global.css for the rules that consume it). This sidesteps
// Tailwind's JIT scanner entirely — since these colors are applied via
// inline style + plain CSS, you can use any hex code you like here without
// needing the literal class name to exist anywhere in the source.

export interface FactionTheme {
  /** Display name shown in the UI. */
  label: string;
  /** Hex color for this faction, e.g. "#34d399". */
  hex: string;
}

const DEFAULT_THEME: FactionTheme = {
  label: 'Unknown',
  hex: '#71717a', 
};

export const FACTION_THEMES: Record<string, FactionTheme> = {
  //Standard
  Town: { label: 'Town', hex: '#5F90C4' },
  Werewolf: { label: 'Werewolves', hex: '#883532' },
  Neutral: { label: 'Neutral', hex: '#B3B3B3' },
  Evil: { label: 'Evil', hex: '#839C38' },
  LesserEvil: { label: 'Lesser Evil', hex: '#8B7884' },
  //Dark
  Village: { label: 'Village', hex: '#5F90C4' },
  Vampire: { label: 'Vampires', hex: '#765D86' },
  //Olympia
  Hero: { label: 'Hero', hex: '#4ade80' },
  Monster: { label: 'Monster', hex: '#839C38' },
  Tainted: { label: 'Tainted', hex: '#883532' },
  Corrupted: { label: 'Corrupted', hex: '#8B7884' },
  //Grimm
  Grim_Folk: { label: 'Folk', hex: '#5F90C4' },
  Grimm_Evil: { label: 'Grimm Evil', hex: '#839C38' },
  Grim_LesserEvil: { label: 'Grim Lesser Evil', hex: '#8B7884' },
  Grim_Fei: { label: 'Fei', hex: '#765D86' },
  Grimm_Neutral: { label: 'Grimm Neutral', hex: '#B3B3B3' },
};

/** Looks up a faction's theme, falling back to a neutral zinc theme for unknown factions. */
export function getFactionTheme(faction?: string | null): FactionTheme {
  return (faction && FACTION_THEMES[faction]) || DEFAULT_THEME;
}
