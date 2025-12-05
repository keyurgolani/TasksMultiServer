import React, { useState } from "react";
import { Typography } from "../../atoms/Typography";
import { Button } from "../../atoms/Button";
import { Toggle } from "../../molecules/Toggle";
import { Badge } from "../../atoms/Badge";
import { Play, RotateCcw, Zap, Heart, Star, Bell } from "lucide-react";

/**
 * AnimationSpeedDemo Component
 *
 * Demonstrates the animation speed effect with interactive elements.
 * Shows buttons and toggles that trigger visible transitions to help
 * developers understand how the speed multiplier affects animations.
 *
 * Requirements: 38.1, 38.2, 38.3, 38.4
 * - Display dedicated animation speed demonstration section
 * - Show interactive elements with visible transitions
 * - Update in real-time when customization engine values change
 * - Include buttons or toggles that trigger animations
 */

export interface AnimationSpeedDemoProps {
  /** Current animation speed value from customization engine (0.5-2.0 multiplier) */
  animationSpeed?: number;
}

export const AnimationSpeedDemo: React.FC<AnimationSpeedDemoProps> = ({
  animationSpeed = 1.0,
}) => {
  // State for interactive elements
  const [toggleStates, setToggleStates] = useState({
    toggle1: false,
    toggle2: true,
    toggle3: false,
  });
  const [pulseActive, setPulseActive] = useState(false);
  const [scaleActive, setScaleActive] = useState(false);
  const [rotateActive, setRotateActive] = useState(false);

  // Calculate actual durations based on animation speed
  const fastDuration = 0.15 / animationSpeed;
  const normalDuration = 0.3 / animationSpeed;
  const slowDuration = 0.5 / animationSpeed;

  const handleToggle = (key: keyof typeof toggleStates) => {
    setToggleStates((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const triggerPulse = () => {
    setPulseActive(true);
    setTimeout(() => setPulseActive(false), slowDuration * 1000);
  };

  const triggerScale = () => {
    setScaleActive(true);
    setTimeout(() => setScaleActive(false), normalDuration * 1000);
  };

  const triggerRotate = () => {
    setRotateActive(true);
    setTimeout(() => setRotateActive(false), slowDuration * 1000);
  };

  return (
    <div className="space-y-6">
      {/* Animation Speed Info */}
      <div className="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]">
        <Zap className="text-[var(--primary)]" size={20} />
        <div>
          <Typography variant="body-sm" color="primary">
            Current Animation Speed: <strong>{animationSpeed.toFixed(2)}x</strong>
          </Typography>
          <Typography variant="caption" color="secondary">
            Fast: {(fastDuration * 1000).toFixed(0)}ms | Normal: {(normalDuration * 1000).toFixed(0)}ms | Slow: {(slowDuration * 1000).toFixed(0)}ms
          </Typography>
        </div>
      </div>

      {/* Interactive Demo Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Toggle Animations */}
        <div className="p-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]">
          <Typography variant="h6" color="primary" className="mb-4">
            Toggle Transitions
          </Typography>
          <div className="space-y-4">
            <Toggle
              checked={toggleStates.toggle1}
              onChange={() => handleToggle("toggle1")}
              label="Smooth Toggle 1"
            />
            <Toggle
              checked={toggleStates.toggle2}
              onChange={() => handleToggle("toggle2")}
              label="Smooth Toggle 2"
            />
            <Toggle
              checked={toggleStates.toggle3}
              onChange={() => handleToggle("toggle3")}
              label="Smooth Toggle 3"
            />
          </div>
          <Typography variant="caption" color="muted" className="mt-3 block">
            Toggle switches use the animation speed for their slide transition
          </Typography>
        </div>

        {/* Button Hover Effects */}
        <div className="p-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]">
          <Typography variant="h6" color="primary" className="mb-4">
            Button Hover Effects
          </Typography>
          <div className="space-y-3">
            <Button
              variant="primary"
              className="w-full"
            >
              Primary Button
            </Button>
            <Button
              variant="secondary"
              className="w-full"
            >
              Secondary Button
            </Button>
            <Button
              variant="ghost"
              className="w-full"
            >
              Ghost Button
            </Button>
          </div>
          <Typography variant="caption" color="muted" className="mt-3 block">
            Hover over buttons to see transition effects
          </Typography>
        </div>

        {/* Triggered Animations */}
        <div className="p-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]">
          <Typography variant="h6" color="primary" className="mb-4">
            Triggered Animations
          </Typography>
          <div className="flex flex-wrap gap-3 mb-4">
            <Button
              variant="secondary"
              size="sm"
              leftIcon={<Play size={14} />}
              onClick={triggerPulse}
            >
              Pulse
            </Button>
            <Button
              variant="secondary"
              size="sm"
              leftIcon={<Zap size={14} />}
              onClick={triggerScale}
            >
              Scale
            </Button>
            <Button
              variant="secondary"
              size="sm"
              leftIcon={<RotateCcw size={14} />}
              onClick={triggerRotate}
            >
              Rotate
            </Button>
          </div>
          <div className="flex justify-center gap-4 py-4">
            <div
              className="w-12 h-12 rounded-lg bg-[var(--primary)] flex items-center justify-center"
              style={{
                transition: `all ${slowDuration}s ease-in-out`,
                transform: pulseActive ? "scale(1.3)" : "scale(1)",
                opacity: pulseActive ? 0.7 : 1,
              }}
            >
              <Heart className="text-white" size={20} />
            </div>
            <div
              className="w-12 h-12 rounded-lg bg-[var(--success)] flex items-center justify-center"
              style={{
                transition: `all ${normalDuration}s ease-in-out`,
                transform: scaleActive ? "scale(1.5)" : "scale(1)",
              }}
            >
              <Star className="text-white" size={20} />
            </div>
            <div
              className="w-12 h-12 rounded-lg bg-[var(--warning)] flex items-center justify-center"
              style={{
                transition: `all ${slowDuration}s ease-in-out`,
                transform: rotateActive ? "rotate(360deg)" : "rotate(0deg)",
              }}
            >
              <Bell className="text-white" size={20} />
            </div>
          </div>
          <Typography variant="caption" color="muted" className="block text-center">
            Click buttons to trigger animations
          </Typography>
        </div>
      </div>


      {/* Badge Animations */}
      <div className="p-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]">
        <Typography variant="h6" color="primary" className="mb-4">
          Badge & Status Transitions
        </Typography>
        <div className="flex flex-wrap gap-3">
          <Badge variant="success">Success</Badge>
          <Badge variant="warning">Warning</Badge>
          <Badge variant="error">Error</Badge>
          <Badge variant="info">Info</Badge>
          <Badge variant="neutral">Neutral</Badge>
        </div>
        <Typography variant="caption" color="muted" className="mt-3 block">
          Badges use animation speed for hover and focus transitions
        </Typography>
      </div>

      {/* Speed Comparison Cards */}
      <div className="p-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]">
        <Typography variant="h6" color="primary" className="mb-4">
          Speed Comparison
        </Typography>
        <Typography variant="caption" color="secondary" className="mb-4 block">
          Hover over the cards below to compare transition speeds
        </Typography>
        <div className="grid grid-cols-3 gap-4">
          {/* Fast */}
          <div
            className="p-4 rounded-lg bg-[var(--bg-app)] border border-[var(--border)] cursor-pointer text-center hover:bg-[var(--primary)] hover:text-white hover:border-[var(--primary)]"
            style={{ transition: `all ${fastDuration}s ease-in-out` }}
          >
            <Typography variant="label" className="block mb-1">Fast</Typography>
            <Typography variant="caption" color="muted">{(fastDuration * 1000).toFixed(0)}ms</Typography>
          </div>
          {/* Normal */}
          <div
            className="p-4 rounded-lg bg-[var(--bg-app)] border border-[var(--border)] cursor-pointer text-center hover:bg-[var(--success)] hover:text-white hover:border-[var(--success)]"
            style={{ transition: `all ${normalDuration}s ease-in-out` }}
          >
            <Typography variant="label" className="block mb-1">Normal</Typography>
            <Typography variant="caption" color="muted">{(normalDuration * 1000).toFixed(0)}ms</Typography>
          </div>
          {/* Slow */}
          <div
            className="p-4 rounded-lg bg-[var(--bg-app)] border border-[var(--border)] cursor-pointer text-center hover:bg-[var(--warning)] hover:text-white hover:border-[var(--warning)]"
            style={{ transition: `all ${slowDuration}s ease-in-out` }}
          >
            <Typography variant="label" className="block mb-1">Slow</Typography>
            <Typography variant="caption" color="muted">{(slowDuration * 1000).toFixed(0)}ms</Typography>
          </div>
        </div>
      </div>

      {/* Current value indicator */}
      <div className="flex items-center gap-2 text-sm">
        <div
          className="w-3 h-3 rounded-full"
          style={{ background: "var(--primary)" }}
        />
        <Typography variant="caption" color="secondary">
          Animation speed multiplier: <strong>{animationSpeed.toFixed(2)}x</strong> — 
          Higher values = faster animations, lower values = slower animations
        </Typography>
      </div>
    </div>
  );
};

export default AnimationSpeedDemo;
