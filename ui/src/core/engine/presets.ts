/**
 * Theme Presets - Built-in Theme Configurations
 * 
 * This module defines the default theme presets for the Refresh UI application.
 * Each preset provides a complete set of theme variables that can be applied
 * as a batch update through the Customization Engine.
 * 
 * Requirement 2.4: Default theme presets (Default, Cyberpunk, Minimal, High Contrast)
 * 
 * @module core/engine/presets
 */

import type { ThemePreset } from './types';

/**
 * Default theme variable values.
 * These serve as the baseline for all presets.
 */
export const defaultThemeVariables: Record<string, string | number> = {
  // Color Variables
  colorPrimary: '#6b73ff',
  colorPrimaryDark: '#5a63e0',
  colorSuccess: '#2ed573',
  colorWarning: '#ffa502',
  colorError: '#ff4757',
  colorInfo: '#3498db',
  
  // Effect Variables
  glassOpacity: 0.7,
  glassBlur: 10,
  glassBorderOpacity: 0.3,
  glowStrength: 50,
  grainOpacity: 0.05,
  parallaxDepth: 20,
  shadowStrength: 40,
  
  // Animation Variables
  animationSpeed: 1,
  
  // Spacing Variables
  borderRadius: 12,
  
  // Typography Variables
  fontFamily: 'default',
};

/**
 * Default Preset
 * 
 * Clean and balanced default theme with subtle glassmorphism effects.
 * Suitable for everyday use with a professional appearance.
 */
export const defaultPreset: ThemePreset = {
  id: 'default',
  name: 'Default',
  description: 'Clean and balanced default theme with subtle glassmorphism effects',
  isBuiltIn: true,
  category: 'light',
  variables: { ...defaultThemeVariables },
};

/**
 * Cyberpunk Preset
 * 
 * Neon-infused futuristic aesthetic with vibrant colors and strong glow effects.
 * Features magenta/cyan color palette with enhanced visual effects for a
 * dynamic, sci-fi inspired experience.
 */
export const cyberpunkPreset: ThemePreset = {
  id: 'cyberpunk',
  name: 'Cyberpunk',
  description: 'Neon-infused futuristic aesthetic with vibrant colors and strong glow effects',
  isBuiltIn: true,
  category: 'dark',
  variables: {
    // Colors - Neon magenta/cyan palette
    colorPrimary: '#ff00ff',
    colorPrimaryDark: '#cc00cc',
    colorSuccess: '#00ff88',
    colorWarning: '#ffaa00',
    colorError: '#ff3366',
    colorInfo: '#00ffff',
    // Effects - Enhanced for cyberpunk feel
    glassOpacity: 0.75,
    glassBlur: 16,
    glassBorderOpacity: 0.4,
    glowStrength: 85,
    grainOpacity: 0.08,
    parallaxDepth: 30,
    shadowStrength: 60,
    // Animation - Slightly faster for dynamic feel
    animationSpeed: 1.15,
    // Spacing - Slightly larger radius for futuristic look
    borderRadius: 16,
    // Typography
    fontFamily: 'default',
  },
};

/**
 * Minimal Preset
 * 
 * Clean and simple design with reduced visual effects for distraction-free focus.
 * Uses monochromatic grayscale colors and sharp corners for a professional,
 * no-nonsense appearance.
 */
export const minimalPreset: ThemePreset = {
  id: 'minimal',
  name: 'Minimal',
  description: 'Clean and simple design with reduced visual effects for distraction-free focus',
  isBuiltIn: true,
  category: 'light',
  variables: {
    // Colors - Monochromatic grayscale
    colorPrimary: '#333333',
    colorPrimaryDark: '#1a1a1a',
    colorSuccess: '#22c55e',
    colorWarning: '#eab308',
    colorError: '#ef4444',
    colorInfo: '#3b82f6',
    // Effects - Minimal to none
    glassOpacity: 0.98,
    glassBlur: 0,
    glassBorderOpacity: 0.1,
    glowStrength: 0,
    grainOpacity: 0,
    parallaxDepth: 0,
    shadowStrength: 20,
    // Animation - Standard speed
    animationSpeed: 1,
    // Spacing - Sharp corners for clean look
    borderRadius: 4,
    // Typography
    fontFamily: 'default',
  },
};

/**
 * High Contrast Preset
 * 
 * Maximum visibility theme designed for accessibility compliance.
 * Uses strong color contrast, pure colors, and clear visual boundaries
 * to ensure readability for users with visual impairments.
 */
export const highContrastPreset: ThemePreset = {
  id: 'high-contrast',
  name: 'High Contrast',
  description: 'Maximum visibility theme designed for accessibility with strong color contrast',
  isBuiltIn: true,
  category: 'dark',
  variables: {
    // Colors - High contrast primary colors
    colorPrimary: '#0066ff',
    colorPrimaryDark: '#0052cc',
    colorSuccess: '#00cc00',
    colorWarning: '#ffcc00',
    colorError: '#ff0000',
    colorInfo: '#00ccff',
    // Effects - Disabled for clarity
    glassOpacity: 0.98,
    glassBlur: 0,
    glassBorderOpacity: 0.8,
    glowStrength: 0,
    grainOpacity: 0,
    parallaxDepth: 0,
    shadowStrength: 0,
    // Animation - Standard speed
    animationSpeed: 1,
    // Spacing - Moderate radius
    borderRadius: 8,
    // Typography
    fontFamily: 'default',
  },
};

/**
 * All built-in theme presets.
 * These presets are always available and cannot be deleted by users.
 */
export const builtInPresets: ThemePreset[] = [
  defaultPreset,
  cyberpunkPreset,
  minimalPreset,
  highContrastPreset,
];

/**
 * Get a preset by its ID.
 * 
 * @param presetId - The ID of the preset to retrieve
 * @returns The preset if found, undefined otherwise
 */
export const getPresetById = (presetId: string): ThemePreset | undefined => {
  return builtInPresets.find((preset) => preset.id === presetId);
};

/**
 * Get all presets in a specific category.
 * 
 * @param category - The category to filter by ('light', 'dark', 'custom')
 * @returns Array of presets in the specified category
 */
export const getPresetsByCategory = (category: string): ThemePreset[] => {
  return builtInPresets.filter((preset) => preset.category === category);
};

/**
 * Check if a preset ID corresponds to a built-in preset.
 * 
 * @param presetId - The ID to check
 * @returns True if the preset is built-in, false otherwise
 */
export const isBuiltInPreset = (presetId: string): boolean => {
  return builtInPresets.some((preset) => preset.id === presetId);
};

/**
 * Get the default theme variables.
 * This is useful for resetting to defaults or creating new presets.
 * 
 * @returns A copy of the default theme variables
 */
export const getDefaultVariables = (): Record<string, string | number> => {
  return { ...defaultThemeVariables };
};
