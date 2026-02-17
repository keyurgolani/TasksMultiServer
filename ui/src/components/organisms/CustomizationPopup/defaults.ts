/**
 * Curated default theme settings
 * These are the recommended defaults that provide a good starting point
 */

import {
  type ColorTheme,
  type FontTheme,
  type EffectSettings,
  colorThemes,
  fontThemes,
  defaultEffectSettings,
} from "../../../styles/themes";

export const curatedDefaultColorScheme: ColorTheme = colorThemes.dark;
export const curatedDefaultTypography: FontTheme = fontThemes.inter;
export const curatedDefaultEffects: EffectSettings = { ...defaultEffectSettings };
