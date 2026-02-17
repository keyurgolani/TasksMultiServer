/**
 * Parallax Shadow Calculation Utilities
 * 
 * Requirements: 39.2, 39.3, 39.4
 * - Parallax shadow is added to base shadow (not replacing it)
 * - Shadow offset is proportional to tilt rotation
 * - Base shadow opacity and blur are maintained
 */

import type { CardVariant } from "./Card";

/**
 * Calculate additive parallax shadow based on tilt rotation
 * 
 * Requirements: 39.2, 39.3, 39.4
 * - Parallax shadow is added to base shadow (not replacing it)
 * - Shadow offset is proportional to tilt rotation
 * - Base shadow opacity and blur are maintained
 * 
 * @param rotateX - X-axis rotation in degrees
 * @param rotateY - Y-axis rotation in degrees
 * @param isHovered - Whether the card is currently hovered
 * @returns CSS box-shadow string for the parallax shadow component
 */
export const calculateParallaxShadow = (
  rotateX: number,
  rotateY: number,
  isHovered: boolean
): string => {
  if (!isHovered) {
    return "none";
  }
  
  // Calculate shadow offset based on rotation
  // Shadow moves opposite to the tilt direction to create depth illusion
  // Scale factor determines how much the shadow moves per degree of rotation
  const shadowScale = 2; // pixels per degree
  const offsetX = -rotateY * shadowScale;
  const offsetY = rotateX * shadowScale;
  
  // Parallax shadow properties
  // Uses a softer, more diffuse shadow to complement the base shadow
  const blur = 20;
  const spread = 0;
  const opacity = 0.15;
  
  return `${offsetX}px ${offsetY}px ${blur}px ${spread}px rgba(0, 0, 0, ${opacity})`;
};

/**
 * Base shadow values for each variant
 * Requirements: 39.1, 39.3 - Maintain base shadow opacity and blur values
 */
export const baseShadows: Record<CardVariant, string> = {
  glass: "var(--glass-shadow)",
  solid: "var(--shadow-md)",
  outline: "none",
};
