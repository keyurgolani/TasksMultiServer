import React, { useCallback, useMemo } from "react";
import { Sparkles, Layers, Move, Zap } from "lucide-react";
import { cn } from "../../../lib/utils";
import { Slider } from "../../molecules/Slider";
import { Typography } from "../../atoms/Typography";
import { type EffectSettings } from "../../../styles/themes";

/**
 * EffectsControlPanel Organism Component
 *
 * A control panel for adjusting visual effects through sliders.
 * Displays controls in a vertical stack layout with grouped sections.
 *
 * Requirements: 31.1, 31.2, 31.3, 31.4, 31.5
 * - Display an effects control panel on the right side of the top half
 * - Display controls in a vertical stack layout
 * - Include sliders for: glass opacity, glass blur, glow strength, grain opacity,
 *   shadow strength, border radius, FAB roundness, parallax strength, animation speed
 * - Update the preview and CSS variables immediately when sliders are adjusted
 * - Group related effects with section headers
 */

export interface EffectsControlPanelProps {
  /** Current effect settings */
  effects: EffectSettings;
  /** Callback fired when an effect value changes */
  onChange: (key: keyof EffectSettings, value: number) => void;
  /** Additional CSS classes */
  className?: string;
  /** Whether the panel is disabled */
  disabled?: boolean;
}

/**
 * Section header component for grouping related controls
 */
interface SectionHeaderProps {
  title: string;
  icon: React.ReactNode;
}

const SectionHeader: React.FC<SectionHeaderProps> = ({ title, icon }) => (
  <div className="flex items-center gap-1.5 mb-2 pb-1.5 border-b border-[var(--border)]">
    <span className="text-[var(--primary)]">{icon}</span>
    <Typography variant="label" color="primary" className="font-semibold text-xs">
      {title}
    </Typography>
  </div>
);

/**
 * Effect control group definitions
 */
interface EffectControl {
  key: keyof EffectSettings;
  label: string;
  min: number;
  max: number;
  step: number;
  unit?: string;
  formatValue?: (value: number) => string;
}

interface EffectGroup {
  id: string;
  title: string;
  icon: React.ReactNode;
  controls: EffectControl[];
}

/**
 * Define the effect groups with their controls
 */
const effectGroups: EffectGroup[] = [
  {
    id: "glass",
    title: "Glass Effects",
    icon: <Layers size={16} />,
    controls: [
      {
        key: "glassOpacity",
        label: "Glass Opacity",
        min: 0,
        max: 100,
        step: 1,
        unit: "%",
      },
      {
        key: "glassBlur",
        label: "Glass Blur",
        min: 0,
        max: 20,
        step: 1,
        unit: "px",
      },
    ],
  },
  {
    id: "visual",
    title: "Visual Effects",
    icon: <Sparkles size={16} />,
    controls: [
      {
        key: "glowStrength",
        label: "Glow Strength",
        min: 0,
        max: 100,
        step: 1,
        unit: "%",
      },
      {
        key: "shadowStrength",
        label: "Shadow Strength",
        min: 0,
        max: 100,
        step: 1,
        unit: "%",
      },
      {
        key: "borderRadius",
        label: "Border Radius",
        min: 0,
        max: 24,
        step: 1,
        unit: "px",
      },
      {
        key: "fabRoundness",
        label: "FAB Roundness",
        min: 0,
        max: 100,
        step: 1,
        unit: "%",
      },
    ],
  },
  {
    id: "motion",
    title: "Motion & Interaction",
    icon: <Move size={16} />,
    controls: [
      {
        key: "parallaxStrength",
        label: "Parallax Strength",
        min: 0,
        max: 100,
        step: 1,
        unit: "%",
      },
      {
        key: "pulsingStrength",
        label: "Pulsing Strength",
        min: 0,
        max: 100,
        step: 1,
        unit: "%",
      },
    ],
  },
  {
    id: "animation",
    title: "Animation",
    icon: <Zap size={16} />,
    controls: [
      {
        key: "animationSpeed",
        label: "Animation Speed",
        min: 0.5,
        max: 2,
        step: 0.1,
        formatValue: (v: number) => `${v.toFixed(1)}x`,
      },
    ],
  },
];

/**
 * EffectsControlPanel component for adjusting visual effects
 *
 * The panel is organized into grouped sections with section headers.
 * Each slider immediately updates the CSS variables when changed,
 * enabling real-time preview updates (Requirement 31.4).
 */
export const EffectsControlPanel: React.FC<EffectsControlPanelProps> = ({
  effects,
  onChange,
  className,
  disabled = false,
}) => {
  /**
   * Create a memoized change handler for each effect key
   * This ensures stable references for the slider callbacks
   */
  const createChangeHandler = useCallback(
    (key: keyof EffectSettings) => (value: number) => {
      onChange(key, value);
    },
    [onChange]
  );

  /**
   * Memoize the rendered groups to prevent unnecessary re-renders
   */
  const renderedGroups = useMemo(
    () =>
      effectGroups.map((group) => (
        <div key={group.id} className="mb-3 last:mb-0">
          <SectionHeader title={group.title} icon={group.icon} />
          <div className="space-y-2">
            {group.controls.map((control) => (
              <Slider
                key={control.key}
                label={control.label}
                value={effects[control.key]}
                onChange={createChangeHandler(control.key)}
                min={control.min}
                max={control.max}
                step={control.step}
                unit={control.unit}
                formatValue={control.formatValue}
                disabled={disabled}
              />
            ))}
          </div>
        </div>
      )),
    [effects, createChangeHandler, disabled]
  );

  return (
    <div
      className={cn(
        "flex flex-col",
        "p-3",
        "bg-[var(--bg-surface)]",
        className
      )}
      data-testid="effects-control-panel"
    >
      {/* Panel header */}
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[var(--border)]">
        <Sparkles size={16} className="text-[var(--primary)]" />
        <Typography variant="label" color="primary" className="font-semibold">
          Effects
        </Typography>
      </div>

      {/* Scrollable content area with vertical stack layout (Requirement 31.2) */}
      <div className="flex-1 overflow-y-auto">
        {renderedGroups}
      </div>
    </div>
  );
};

EffectsControlPanel.displayName = "EffectsControlPanel";

export default EffectsControlPanel;
