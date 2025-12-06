import React, { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Check, RotateCcw } from "lucide-react";
import { cn } from "../../../lib/utils";
import { LivePreviewPanel } from "../LivePreviewPanel";
import { EffectsControlPanel } from "../EffectsControlPanel";
import { ColorSchemeRow } from "../../molecules/ColorSchemeRow";
import { TypographyRow } from "../../molecules/TypographyRow";
import { Typography } from "../../atoms/Typography";
import { Button } from "../../atoms/Button";
import {
  type ColorTheme,
  type FontTheme,
  type EffectSettings,
  colorThemes,
  fontThemes,
  defaultEffectSettings,
} from "../../../styles/themes";

/**
 * Curated default theme settings
 * These are the recommended defaults that provide a good starting point
 */
export const curatedDefaultColorScheme = colorThemes.dark;
export const curatedDefaultTypography = fontThemes.inter;
export const curatedDefaultEffects: EffectSettings = { ...defaultEffectSettings };

/**
 * CustomizationPopup Organism Component
 *
 * A centered modal popup for customizing the UI appearance. The popup is divided
 * into two halves:
 * - Top half: LivePreviewPanel (left) and EffectsControlPanel (right)
 * - Bottom half: ColorSchemeRow and TypographyRow
 *
 * Requirements: 29.1, 29.2, 29.3, 29.4, 29.5, 52.1, 52.2, 52.3, 52.4, 52.5
 * - Display a wide rectangular modal centered on the screen
 * - Dim and blur the background according to current glassmorphism settings
 * - Divide layout into top half (preview and effects) and bottom half (color and typography)
 * - Close popup when clicking outside (treated as Cancel - discards changes)
 * - Apply glassmorphism effect consistent with the design system
 * - Display Apply and Cancel buttons in the footer
 * - Apply button applies all changes to main UI and closes popup
 * - Cancel button discards all changes and closes popup
 * - Changes only affect preview until Apply is clicked
 */

export interface CustomizationPopupProps {
  /** Whether the popup is open */
  isOpen: boolean;
  /** Callback when the popup should close */
  onClose: () => void;
  /** Current color scheme */
  colorScheme?: ColorTheme;
  /** Current typography scheme */
  typography?: FontTheme;
  /** Current effect settings */
  effects?: EffectSettings;
  /** Callback when color scheme changes */
  onColorSchemeChange?: (scheme: ColorTheme) => void;
  /** Callback when typography changes */
  onTypographyChange?: (typography: FontTheme) => void;
  /** Callback when effects change */
  onEffectsChange?: (key: keyof EffectSettings, value: number) => void;
  /** Callback when all changes are applied (Apply button clicked) */
  onApply?: (colorScheme: ColorTheme, typography: FontTheme, effects: EffectSettings) => void;
  /** Callback when reset to defaults is clicked - resets all settings to curated defaults */
  onResetToDefaults?: () => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * CustomizationPopup component for theme customization
 * 
 * Requirements: 52.1, 52.2, 52.3, 52.4, 52.5
 * - Changes only affect the preview until Apply is clicked
 * - Apply button applies all changes and closes popup
 * - Cancel button discards changes and closes popup
 * - Outside click is treated as Cancel (discards changes)
 */
/**
 * Inner component that handles the popup content
 * This is remounted each time the popup opens via key prop, ensuring fresh state
 * Changes only affect local preview state until Apply is clicked (Requirement 52.4)
 */
const CustomizationPopupContent: React.FC<CustomizationPopupProps> = ({
  isOpen,
  onClose,
  colorScheme = colorThemes.dark,
  typography = fontThemes.inter,
  effects = defaultEffectSettings,
  onColorSchemeChange,
  onTypographyChange,
  onEffectsChange,
  onApply,
  onResetToDefaults,
  className,
}) => {
  const popupRef = useRef<HTMLDivElement>(null);
  
  // Local state for preview-only changes (Requirement 52.4)
  // Initialize with current props - these will be the "pending" changes
  const [pendingColorScheme, setPendingColorScheme] = useState<ColorTheme>(colorScheme);
  const [pendingTypography, setPendingTypography] = useState<FontTheme>(typography);
  const [pendingEffects, setPendingEffects] = useState<EffectSettings>(effects);

  // Handle Cancel action - discard changes and close (Requirement 52.3)
  // Since changes only affect local preview state (not the main UI), we just close the popup
  // The main UI remains unchanged because we never called the parent callbacks during editing
  const handleCancel = useCallback(() => {
    onClose();
  }, [onClose]);

  // Handle Apply action - apply all changes to main UI (Requirement 52.2)
  const handleApply = useCallback(() => {
    // Apply all pending changes to the main UI via callbacks
    if (onColorSchemeChange) {
      onColorSchemeChange(pendingColorScheme);
    }
    if (onTypographyChange) {
      onTypographyChange(pendingTypography);
    }
    if (onEffectsChange) {
      // Apply each effect setting
      Object.keys(pendingEffects).forEach((key) => {
        const effectKey = key as keyof EffectSettings;
        onEffectsChange(effectKey, pendingEffects[effectKey]);
      });
    }
    // Also call the onApply callback if provided
    if (onApply) {
      onApply(pendingColorScheme, pendingTypography, pendingEffects);
    }
    onClose();
  }, [pendingColorScheme, pendingTypography, pendingEffects, onColorSchemeChange, onTypographyChange, onEffectsChange, onApply, onClose]);

  // Handle Reset to Defaults action - restore curated default values in preview only (Requirements 10.1, 10.2, 10.3)
  // The main UI will only change when the user clicks Apply
  const handleResetToDefaults = useCallback(() => {
    // Update local preview state to defaults - this only affects the preview panel
    // The main UI remains unchanged until the user clicks Apply
    setPendingColorScheme(curatedDefaultColorScheme);
    setPendingTypography(curatedDefaultTypography);
    setPendingEffects({ ...curatedDefaultEffects });
    
    // Call the onResetToDefaults callback if provided (for any additional handling)
    if (onResetToDefaults) {
      onResetToDefaults();
    }
  }, [onResetToDefaults]);

  // Handle outside click - treat as Cancel (Requirement 52.5)
  const handleOutsideClick = useCallback(() => {
    handleCancel();
  }, [handleCancel]);

  // Handle escape key to close (treat as Cancel)
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        handleCancel();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, handleCancel]);

  // Prevent body scroll when popup is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  // Handle color scheme selection - updates preview only (Requirement 52.4)
  // Changes are stored in local state and only applied to main UI when Apply is clicked
  const handleColorSchemeSelect = useCallback(
    (schemeId: string) => {
      const scheme = colorThemes[schemeId];
      if (scheme) {
        setPendingColorScheme(scheme);
        // Do NOT call onColorSchemeChange here - changes only affect preview until Apply is clicked
      }
    },
    []
  );

  // Handle typography selection - updates preview only (Requirement 52.4)
  // Changes are stored in local state and only applied to main UI when Apply is clicked
  const handleTypographySelect = useCallback(
    (optionId: string) => {
      const font = fontThemes[optionId];
      if (font) {
        setPendingTypography(font);
        // Do NOT call onTypographyChange here - changes only affect preview until Apply is clicked
      }
    },
    []
  );

  // Handle effects change - updates preview only (Requirement 52.4)
  // Changes are stored in local state and only applied to main UI when Apply is clicked
  const handleEffectsChange = useCallback(
    (key: keyof EffectSettings, value: number) => {
      setPendingEffects((prev) => ({
        ...prev,
        [key]: value,
      }));
      // Do NOT call onEffectsChange here - changes only affect preview until Apply is clicked
    },
    []
  );

  // Convert theme objects to arrays for the row components
  const colorSchemeArray = Object.values(colorThemes);
  const typographyArray = Object.values(fontThemes);

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          className={cn(
            "fixed inset-0 z-50 flex items-center justify-center"
          )}
          role="dialog"
          aria-modal="true"
          aria-labelledby="customization-popup-title"
          data-testid="customization-popup-backdrop"
        >
          {/* Background dim and blur (Requirement 29.2) - clicking closes popup as Cancel (Requirement 52.5) */}
          <motion.div
            className="absolute inset-0 cursor-pointer"
            style={{
              backgroundColor: `rgba(0, 0, 0, ${0.5 + (pendingEffects.glassOpacity / 100) * 0.3})`,
              backdropFilter: `blur(${Math.min(pendingEffects.glassBlur, 8)}px)`,
            }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={handleOutsideClick}
            data-testid="customization-popup-overlay"
            aria-hidden="true"
          />

          {/* Popup container (Requirement 29.1, 29.5) */}
          <motion.div
            ref={popupRef}
            className={cn(
              "relative z-10 flex flex-col",
              "w-[90vw] max-w-[1200px] h-[92vh] max-h-[900px]",
              "rounded-xl overflow-hidden",
              "border border-[var(--border)]",
              "shadow-2xl",
              className
            )}
            style={{
              // Glassmorphism effect (Requirement 29.5)
              backgroundColor: `rgba(var(--bg-surface-rgb, 30, 33, 40), ${pendingEffects.glassOpacity / 100})`,
              backdropFilter: `blur(${pendingEffects.glassBlur}px)`,
            }}
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            data-testid="customization-popup"
          >
            {/* Header */}
            <div
              className="flex items-center justify-between px-6 py-3 border-b border-[var(--border)]"
              style={{ backgroundColor: "var(--bg-surface)" }}
            >
              <Typography
                id="customization-popup-title"
                variant="h5"
                color="primary"
              >
                Customize Appearance
              </Typography>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCancel}
                aria-label="Close customization popup"
              >
                <X size={20} />
              </Button>
            </div>

            {/* Content area - horizontal layout with effects panel spanning full height */}
            <div className="flex-1 flex overflow-hidden">
              {/* Left side: Preview and selection rows */}
              <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                {/* Preview area */}
                <div
                  className="flex-1 p-3 min-h-0"
                  data-testid="customization-popup-top"
                >
                  <LivePreviewPanel
                    colorScheme={pendingColorScheme}
                    typography={pendingTypography}
                    effects={pendingEffects}
                    className="h-full"
                    title="Preview"
                  />
                </div>

                {/* Bottom: Color and Typography selection (Requirement 29.3) */}
                <div
                  className="flex-shrink-0 border-t border-[var(--border)] px-3 py-2 space-y-2"
                  style={{ backgroundColor: "var(--bg-surface)" }}
                  data-testid="customization-popup-bottom"
                >
                  {/* Color Scheme Row */}
                  <div>
                    <Typography
                      variant="label"
                      color="secondary"
                      className="mb-1 block text-xs"
                    >
                      Color Scheme
                    </Typography>
                    <ColorSchemeRow
                      schemes={colorSchemeArray}
                      selectedSchemeId={pendingColorScheme.id}
                      onSelect={handleColorSchemeSelect}
                      autoScrollToSelected
                    />
                  </div>

                  {/* Typography Row */}
                  <div>
                    <Typography
                      variant="label"
                      color="secondary"
                      className="mb-1 block text-xs"
                    >
                      Typography
                    </Typography>
                    <TypographyRow
                      options={typographyArray}
                      selectedOptionId={pendingTypography.id}
                      onSelect={handleTypographySelect}
                      autoScrollToSelected
                    />
                  </div>
                </div>
              </div>

              {/* Right side: Effects Control Panel - spans full height */}
              <div 
                className="w-[280px] flex-shrink-0 border-l border-[var(--border)] overflow-y-auto scrollbar-hide"
                style={{ backgroundColor: "var(--bg-surface)" }}
              >
                <EffectsControlPanel
                  effects={pendingEffects}
                  onChange={handleEffectsChange}
                  className="h-full"
                />
              </div>
            </div>

            {/* Footer with Reset to Defaults, Apply and Cancel buttons (Requirements 10.1, 52.1) */}
            <div
              className="flex-shrink-0 flex items-center justify-between px-6 py-3 border-t border-[var(--border)]"
              style={{ backgroundColor: "var(--bg-surface)" }}
              data-testid="customization-popup-footer"
            >
              {/* Reset to Defaults button on the left (Requirement 10.1) */}
              <Button
                variant="ghost"
                size="md"
                onClick={handleResetToDefaults}
                data-testid="customization-popup-reset"
                title="Reset all settings to curated default values"
              >
                <RotateCcw size={16} className="mr-2" />
                Reset to Defaults
              </Button>
              
              {/* Apply and Cancel buttons on the right */}
              <div className="flex items-center gap-3">
                <Button
                  variant="secondary"
                  size="md"
                  onClick={handleCancel}
                  data-testid="customization-popup-cancel"
                >
                  <X size={16} className="mr-2" />
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="md"
                  onClick={handleApply}
                  data-testid="customization-popup-apply"
                >
                  <Check size={16} className="mr-2" />
                  Apply
                </Button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

CustomizationPopupContent.displayName = "CustomizationPopupContent";

/**
 * Custom hook to generate a new key each time the popup opens
 * This ensures the content component is remounted with fresh state
 */
function useOpenKey(isOpen: boolean): number {
  const [key, setKey] = React.useState(0);
  const wasOpenRef = React.useRef(isOpen);
  
  React.useEffect(() => {
    if (isOpen && !wasOpenRef.current) {
      // Popup just opened - increment key to remount content
      setKey(prev => prev + 1);
    }
    wasOpenRef.current = isOpen;
  }, [isOpen]);
  
  return key;
}

/**
 * CustomizationPopup wrapper component
 * 
 * This wrapper uses a key that increments each time the popup opens,
 * ensuring the content component is remounted with fresh local state.
 * Changes only affect the preview until Apply is clicked (Requirement 52.4).
 * 
 * Requirements: 52.1, 52.2, 52.3, 52.4, 52.5
 */
export const CustomizationPopup: React.FC<CustomizationPopupProps> = ({
  isOpen,
  onClose,
  colorScheme = colorThemes.dark,
  typography = fontThemes.inter,
  effects = defaultEffectSettings,
  onColorSchemeChange,
  onTypographyChange,
  onEffectsChange,
  onApply,
  onResetToDefaults,
  className,
}) => {
  // Generate a new key each time the popup opens to ensure fresh state
  const key = useOpenKey(isOpen);
  
  if (!isOpen) {
    return null;
  }
  
  return (
    <CustomizationPopupContent
      key={key}
      isOpen={isOpen}
      onClose={onClose}
      colorScheme={colorScheme}
      typography={typography}
      effects={effects}
      onColorSchemeChange={onColorSchemeChange}
      onTypographyChange={onTypographyChange}
      onEffectsChange={onEffectsChange}
      onApply={onApply}
      onResetToDefaults={onResetToDefaults}
      className={className}
    />
  );
};

CustomizationPopup.displayName = "CustomizationPopup";

export default CustomizationPopup;
