import React, { useState, useRef, useEffect } from "react";
import { Palette, ChevronDown } from "lucide-react";
import { 
  colorThemes, 
  fontThemes, 
  type EffectSettings 
} from "../styles/themes";
import { useTheme } from "../context/ThemeContext";
import { ThemePreview } from "./ThemePreview";
import styles from "./ThemeSelector.module.css";

export const ThemeSelector: React.FC = () => {
  const { 
    activeColorTheme, 
    activeFontTheme, 
    activeEffectSettings,
    setColorTheme, 
    setFontTheme, 
    setEffectSettings 
  } = useTheme();

  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Local state for preview
  const [localColorId, setLocalColorId] = useState(activeColorTheme.id);
  const [localFontId, setLocalFontId] = useState(activeFontTheme.id);
  const [localEffects, setLocalEffects] = useState<EffectSettings>(activeEffectSettings);



  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleToggle = () => {
    if (!isOpen) {
      // Reset to current active state when opening
      setLocalColorId(activeColorTheme.id);
      setLocalFontId(activeFontTheme.id);
      setLocalEffects(activeEffectSettings);
    }
    setIsOpen(!isOpen);
  };

  const handleApply = () => {
    setColorTheme(localColorId);
    setFontTheme(localFontId);
    setEffectSettings(localEffects);
    setIsOpen(false);
  };

  const handleUpdateEffect = (key: keyof EffectSettings, value: number) => {
    setLocalEffects(prev => ({ ...prev, [key]: value }));
  };

  const previewColorTheme = colorThemes[localColorId] || colorThemes.light;
  const previewFontTheme = fontThemes[localFontId] || fontThemes.inter;

  return (
    <div className={styles.container} ref={containerRef}>
      <button className={styles.trigger} onClick={handleToggle}>
        <span className={styles.icon}>
          <Palette size={16} />
        </span>
        <span>Theme</span>
        <ChevronDown size={14} />
      </button>

      {isOpen && (
        <div className={styles.dropdown}>
          {/* Preview Section */}
          <div className={styles.previewSection}>
            <ThemePreview 
              colorTheme={previewColorTheme}
              fontTheme={previewFontTheme}
              effectSettings={localEffects}
            />
          </div>

          {/* Controls Section */}
          <div className={styles.controlsSection}>
            
            {/* Colors */}
            <div>
              <div className={styles.sectionTitle}>Colors</div>
              <div className={styles.scrollRow}>
                {Object.values(colorThemes).map((theme) => (
                  <div
                    key={theme.id}
                    className={`${styles.colorOption} ${
                      localColorId === theme.id ? styles.active : ""
                    }`}
                    onClick={() => setLocalColorId(theme.id)}
                    title={theme.name}
                  >
                    <div 
                      className={styles.colorPreview}
                      style={{ background: theme.colors.bgApp }}
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Fonts */}
            <div>
              <div className={styles.sectionTitle}>Fonts</div>
              <div className={styles.scrollRow}>
                {Object.values(fontThemes).map((theme) => (
                  <div
                    key={theme.id}
                    className={`${styles.fontOption} ${
                      localFontId === theme.id ? styles.active : ""
                    }`}
                    onClick={() => setLocalFontId(theme.id)}
                    style={{ fontFamily: theme.fontFamily }}
                  >
                    {theme.name}
                  </div>
                ))}
              </div>
            </div>

            {/* Effects */}
            <div>
              <div className={styles.sectionTitle}>Effects</div>
              <div className={styles.effectControl}>
                <div className={styles.effectLabel}>
                  <span>Glow Strength</span>
                  <span>{localEffects.glowStrength}%</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="100" 
                  value={localEffects.glowStrength}
                  onChange={(e) => handleUpdateEffect('glowStrength', parseInt(e.target.value))}
                  className={styles.rangeInput}
                />
              </div>

              <div className={styles.effectControl}>
                <div className={styles.effectLabel}>
                  <span>Glass Opacity</span>
                  <span>{localEffects.glassOpacity}%</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="100" 
                  value={localEffects.glassOpacity}
                  onChange={(e) => handleUpdateEffect('glassOpacity', parseInt(e.target.value))}
                  className={styles.rangeInput}
                />
              </div>

              <div className={styles.effectControl}>
                <div className={styles.effectLabel}>
                  <span>Glass Blur</span>
                  <span>{localEffects.glassBlur}px</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="20" 
                  value={localEffects.glassBlur}
                  onChange={(e) => handleUpdateEffect('glassBlur', parseInt(e.target.value))}
                  className={styles.rangeInput}
                />
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className={styles.footer}>
            <button 
              className={`${styles.button} ${styles.buttonSecondary}`}
              onClick={() => setIsOpen(false)}
            >
              Cancel
            </button>
            <button 
              className={`${styles.button} ${styles.buttonPrimary}`}
              onClick={handleApply}
            >
              Apply Changes
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
