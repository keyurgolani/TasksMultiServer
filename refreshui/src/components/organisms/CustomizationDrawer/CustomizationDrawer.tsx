import React, { useState, useEffect, useRef } from "react";
import { X, Check, Palette, Type, Sparkles, RotateCcw } from "lucide-react";
import { Typography } from "../../atoms/Typography";
import { Slider } from "../../molecules/Slider";
import { useTheme } from "../../../context/ThemeContext";
import {
  colorThemes,
  fontThemes,
  defaultEffectSettings,
  type EffectSettings,
} from "../../../styles/themes";
import { cn } from "../../../lib/utils";

/**
 * @deprecated Use CustomizationPopup instead (Requirement 53.2)
 * 
 * CustomizationDrawer Organism Component
 *
 * A drawer component providing grouped sliders and toggles for all
 * customizable design tokens. Allows real-time visual customization
 * of the UI.
 *
 * NOTE: This component is deprecated and will be removed in a future version.
 * Please use CustomizationPopup instead, which provides a better user experience
 * with a centered modal layout, live preview, and improved organization.
 *
 * Requirements: 5.4
 * - Provide grouped sliders and toggles for all customizable design tokens
 * - Support color theme selection
 * - Support font theme selection
 * - Support effect settings (glow, glass, parallax, animation speed, etc.)
 *
 * Groups:
 * - Color Themes
 * - Typography
 * - Interface Effects (glow, glass, shadows, borders)
 * - Animation & Motion
 */

export interface CustomizationDrawerProps {
  /** Whether the drawer is open */
  isOpen: boolean;
  /** Callback fired when the drawer should close */
  onClose: () => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Control group component for organizing related controls
 */
interface ControlGroupProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultExpanded?: boolean;
}

const ControlGroup: React.FC<ControlGroupProps> = ({
  title,
  icon,
  children,
  defaultExpanded = true,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="border-b border-[var(--border)] last:border-b-0">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "w-full flex items-center gap-3 px-4 py-3",
          "text-left transition-colors duration-[calc(var(--duration-fast)*1s)]",
          "hover:bg-[var(--bg-surface-hover)]"
        )}
        aria-expanded={isExpanded}
      >
        <span className="text-[var(--primary)]">{icon}</span>
        <Typography variant="label" color="primary" className="flex-1">
          {title}
        </Typography>
        <svg
          className={cn(
            "w-4 h-4 text-[var(--text-muted)] transition-transform duration-200",
            isExpanded && "rotate-180"
          )}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      {isExpanded && (
        <div className="px-4 pb-4 space-y-4">{children}</div>
      )}
    </div>
  );
};

/**
 * Color theme option component
 */
interface ColorOptionProps {
  theme: (typeof colorThemes)[string];
  isSelected: boolean;
  onClick: () => void;
}

const ColorOption: React.FC<ColorOptionProps> = ({
  theme,
  isSelected,
  onClick,
}) => (
  <button
    type="button"
    onClick={onClick}
    className={cn(
      "relative w-16 h-12 rounded-lg overflow-hidden",
      "border-2 transition-all duration-200",
      "hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary)]",
      isSelected
        ? "border-[var(--primary)] shadow-[0_0_8px_var(--glow-primary)]"
        : "border-transparent"
    )}
    title={theme.name}
    aria-label={`Select ${theme.name} color theme`}
    aria-pressed={isSelected}
  >
    <div className="flex h-full">
      <div
        className="w-1/3 h-full"
        style={{ backgroundColor: theme.colors.bgSurface }}
      />
      <div
        className="flex-1 h-full flex flex-col p-1 gap-1"
        style={{ backgroundColor: theme.colors.bgApp }}
      >
        <div
          className="w-full h-2 rounded-sm"
          style={{ backgroundColor: theme.colors.bgSurface }}
        />
        <div
          className="w-3/4 h-3 rounded-sm mt-auto ml-auto"
          style={{ backgroundColor: theme.colors.primary }}
        />
      </div>
    </div>
    {isSelected && (
      <div className="absolute inset-0 flex items-center justify-center bg-black/20">
        <Check size={14} className="text-white" />
      </div>
    )}
  </button>
);

/**
 * Font theme option component
 */
interface FontOptionProps {
  theme: (typeof fontThemes)[string];
  isSelected: boolean;
  onClick: () => void;
}

const FontOption: React.FC<FontOptionProps> = ({
  theme,
  isSelected,
  onClick,
}) => (
  <button
    type="button"
    onClick={onClick}
    className={cn(
      "px-3 py-2 rounded-lg border transition-all duration-200",
      "hover:bg-[var(--bg-surface-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary)]",
      isSelected
        ? "border-[var(--primary)] bg-[var(--primary)] text-white"
        : "border-[var(--border)] text-[var(--text-primary)]"
    )}
    style={{ fontFamily: theme.fontFamily }}
    title={`${theme.name} (${theme.category})`}
    aria-label={`Select ${theme.name} font`}
    aria-pressed={isSelected}
  >
    <span className="text-sm font-medium">{theme.name}</span>
  </button>
);

/**
 * CustomizationDrawer component for theme and effect customization
 */
export const CustomizationDrawer: React.FC<CustomizationDrawerProps> = ({
  isOpen,
  onClose,
  className,
}) => {
  const {
    activeColorTheme,
    activeFontTheme,
    activeEffectSettings,
    setColorTheme,
    setFontTheme,
    setEffectSettings,
  } = useTheme();

  // Local state for preview (changes applied on close or explicit apply)
  const [localColorId, setLocalColorId] = useState(activeColorTheme.id);
  const [localFontId, setLocalFontId] = useState(activeFontTheme.id);
  const [localEffects, setLocalEffects] = useState<EffectSettings>(activeEffectSettings);

  // Ref for drawer element
  const drawerRef = useRef<HTMLDivElement>(null);

  // Track previous isOpen state to detect when drawer opens
  const prevIsOpenRef = useRef(isOpen);
  
  // Sync local state when drawer opens - using layout effect to sync before paint
  useEffect(() => {
    const wasOpen = prevIsOpenRef.current;
    prevIsOpenRef.current = isOpen;
    
    // Only sync when drawer transitions from closed to open
    if (isOpen && !wasOpen) {
      // Use requestAnimationFrame to defer state updates
      requestAnimationFrame(() => {
        setLocalColorId(activeColorTheme.id);
        setLocalFontId(activeFontTheme.id);
        setLocalEffects(activeEffectSettings);
      });
    }
  }, [isOpen, activeColorTheme.id, activeFontTheme.id, activeEffectSettings]);

  // Handle escape key to close drawer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Apply changes immediately for live preview
  useEffect(() => {
    if (isOpen) {
      setColorTheme(localColorId);
      setFontTheme(localFontId);
      setEffectSettings(localEffects);
    }
  }, [isOpen, localColorId, localFontId, localEffects, setColorTheme, setFontTheme, setEffectSettings]);

  /**
   * Update a single effect setting
   */
  const handleEffectChange = (key: keyof EffectSettings, value: number) => {
    setLocalEffects((prev) => ({ ...prev, [key]: value }));
  };

  /**
   * Reset all effects to defaults
   */
  const handleResetEffects = () => {
    setLocalEffects(defaultEffectSettings);
  };

  /**
   * Check if effects have been modified from defaults
   */
  const hasModifiedEffects = Object.keys(defaultEffectSettings).some(
    (key) =>
      localEffects[key as keyof EffectSettings] !==
      defaultEffectSettings[key as keyof EffectSettings]
  );

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className={cn(
          "fixed inset-0 bg-black/50 backdrop-blur-sm z-40",
          "animate-in fade-in duration-200"
        )}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-label="Customization drawer"
        className={cn(
          "fixed right-0 top-0 bottom-0 z-50",
          "w-[380px] max-w-[90vw]",
          "bg-[var(--bg-surface)] border-l border-[var(--border)]",
          "shadow-[-8px_0_32px_rgba(0,0,0,0.2)]",
          "flex flex-col",
          "animate-in slide-in-from-right duration-300",
          className
        )}
        data-testid="customization-drawer"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)]">
          <Typography variant="h6" color="primary">
            Customizations
          </Typography>
          <button
            type="button"
            onClick={onClose}
            className={cn(
              "p-2 rounded-full transition-colors duration-200",
              "hover:bg-[var(--bg-surface-hover)]",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary)]"
            )}
            aria-label="Close customization drawer"
          >
            <X size={20} className="text-[var(--text-secondary)]" />
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto">
          {/* Color Themes */}
          <ControlGroup
            title="Color Theme"
            icon={<Palette size={18} />}
            defaultExpanded={true}
          >
            <div className="flex flex-wrap gap-2">
              {Object.values(colorThemes).map((theme) => (
                <ColorOption
                  key={theme.id}
                  theme={theme}
                  isSelected={localColorId === theme.id}
                  onClick={() => setLocalColorId(theme.id)}
                />
              ))}
            </div>
          </ControlGroup>

          {/* Typography */}
          <ControlGroup
            title="Typography"
            icon={<Type size={18} />}
            defaultExpanded={true}
          >
            <div className="flex flex-wrap gap-2">
              {Object.values(fontThemes).map((theme) => (
                <FontOption
                  key={theme.id}
                  theme={theme}
                  isSelected={localFontId === theme.id}
                  onClick={() => setLocalFontId(theme.id)}
                />
              ))}
            </div>
          </ControlGroup>

          {/* Interface Effects */}
          <ControlGroup
            title="Interface Effects"
            icon={<Sparkles size={18} />}
            defaultExpanded={true}
          >
            <div className="space-y-5">
              <Slider
                label="Glow Strength"
                value={localEffects.glowStrength}
                onChange={(value) => handleEffectChange("glowStrength", value)}
                min={0}
                max={100}
                step={1}
                unit="%"
              />

              <Slider
                label="Glass Opacity"
                value={localEffects.glassOpacity}
                onChange={(value) => handleEffectChange("glassOpacity", value)}
                min={0}
                max={100}
                step={1}
                unit="%"
              />

              <Slider
                label="Glass Blur"
                value={localEffects.glassBlur}
                onChange={(value) => handleEffectChange("glassBlur", value)}
                min={0}
                max={20}
                step={1}
                unit="px"
              />

              <Slider
                label="Shadow Strength"
                value={localEffects.shadowStrength}
                onChange={(value) => handleEffectChange("shadowStrength", value)}
                min={0}
                max={100}
                step={1}
                unit="%"
              />

              <Slider
                label="Border Radius"
                value={localEffects.borderRadius}
                onChange={(value) => handleEffectChange("borderRadius", value)}
                min={0}
                max={24}
                step={1}
                unit="px"
              />

              <Slider
                label="FAB Roundness"
                value={localEffects.fabRoundness}
                onChange={(value) => handleEffectChange("fabRoundness", value)}
                min={0}
                max={100}
                step={1}
                unit="%"
              />

              <Slider
                label="Parallax Strength"
                value={localEffects.parallaxStrength}
                onChange={(value) => handleEffectChange("parallaxStrength", value)}
                min={0}
                max={100}
                step={1}
                unit="%"
              />

              <Slider
                label="Animation Speed"
                value={localEffects.animationSpeed}
                onChange={(value) => handleEffectChange("animationSpeed", value)}
                min={0.5}
                max={2}
                step={0.1}
                formatValue={(v) => `${v.toFixed(1)}x`}
              />
            </div>
          </ControlGroup>
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-[var(--border)] flex items-center justify-between">
          <button
            type="button"
            onClick={handleResetEffects}
            disabled={!hasModifiedEffects}
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-lg",
              "text-sm font-medium transition-colors duration-200",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary)]",
              hasModifiedEffects
                ? "text-[var(--text-secondary)] hover:bg-[var(--bg-surface-hover)]"
                : "text-[var(--text-muted)] cursor-not-allowed opacity-50"
            )}
            aria-label="Reset effects to defaults"
          >
            <RotateCcw size={16} />
            Reset Effects
          </button>

          <button
            type="button"
            onClick={onClose}
            className={cn(
              "px-4 py-2 rounded-lg",
              "bg-[var(--primary)] text-white",
              "text-sm font-medium transition-all duration-200",
              "hover:bg-[var(--primary-dark)]",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary)] focus-visible:ring-offset-2"
            )}
          >
            Done
          </button>
        </div>
      </div>
    </>
  );
};

CustomizationDrawer.displayName = "CustomizationDrawer";

export default CustomizationDrawer;
