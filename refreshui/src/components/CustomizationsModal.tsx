import React, { useState, useEffect, useRef } from "react";
import { X, Check } from "lucide-react";
import { 
  colorThemes, 
  fontThemes, 
  type EffectSettings 
} from "../styles/themes";
import { useTheme } from "../context/ThemeContext";
import { ThemePreview } from "./ThemePreview";
import styles from "./CustomizationsModal.module.css";

interface CustomizationsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CustomizationsModal: React.FC<CustomizationsModalProps> = ({
  isOpen,
  onClose
}) => {
  const { 
    activeColorTheme, 
    activeFontTheme, 
    activeEffectSettings,
    setColorTheme, 
    setFontTheme, 
    setEffectSettings 
  } = useTheme();

  // Local state for preview
  const [localColorId, setLocalColorId] = useState(activeColorTheme.id);
  const [localFontId, setLocalFontId] = useState(activeFontTheme.id);
  const [localEffects, setLocalEffects] = useState<EffectSettings>(activeEffectSettings);

  // Refs for auto-scrolling to active items
  const activeColorRef = useRef<HTMLDivElement>(null);
  const activeFontRef = useRef<HTMLDivElement>(null);

  // Reset local state when modal opens
  useEffect(() => {
    if (isOpen) {
      setLocalColorId(activeColorTheme.id);
      setLocalFontId(activeFontTheme.id);
      setLocalEffects(activeEffectSettings);

      // Scroll to active items after a short delay to ensure DOM is ready
      setTimeout(() => {
        activeColorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        activeFontRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      }, 100);
    }
  }, [isOpen, activeColorTheme.id, activeFontTheme.id, activeEffectSettings]);

  const handleApply = () => {
    setColorTheme(localColorId);
    setFontTheme(localFontId);
    setEffectSettings(localEffects);
    onClose();
  };

  const handleUpdateEffect = (key: keyof EffectSettings, value: number) => {
    setLocalEffects(prev => ({ ...prev, [key]: value }));
  };

  if (!isOpen) return null;

  const previewColorTheme = colorThemes[localColorId] || colorThemes.light;
  const previewFontTheme = fontThemes[localFontId] || fontThemes.inter;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <div className={styles.title}>
            Customizations
          </div>
          <button className={styles.closeButton} onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className={styles.mainContent}>
          {/* Top Left: Preview Area */}
          <div className={styles.previewArea}>
            <div className={styles.previewWrapper}>
              <ThemePreview 
                colorTheme={previewColorTheme}
                fontTheme={previewFontTheme}
                effectSettings={localEffects}
              />
            </div>
          </div>

          {/* Right Side: Effects Panel */}
          <div className={styles.effectsPanel}>
            <div className={styles.sectionTitle}>Interface Effects</div>
            
            <div className={styles.effectControl}>
              <div className={styles.effectHeader}>
                <span>Glow Strength</span>
                <span className={styles.effectValue}>{localEffects.glowStrength}%</span>
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
              <div className={styles.effectHeader}>
                <span>Glass Opacity</span>
                <span className={styles.effectValue}>{localEffects.glassOpacity}%</span>
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
              <div className={styles.effectHeader}>
                <span>Glass Blur</span>
                <span className={styles.effectValue}>{localEffects.glassBlur}px</span>
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

            <div className={styles.effectControl}>
              <div className={styles.effectHeader}>
                <span>FAB Roundness</span>
                <span className={styles.effectValue}>{localEffects.fabRoundness}%</span>
              </div>
              <input 
                type="range" 
                min="0" 
                max="100" 
                value={localEffects.fabRoundness}
                onChange={(e) => handleUpdateEffect('fabRoundness', parseInt(e.target.value))}
                className={styles.rangeInput}
              />
            </div>
          </div>

          {/* Bottom Left: Colors & Fonts */}
          <div className={styles.bottomControls}>
            {/* Colors */}
            <div>
              <div className={styles.sectionTitle}>Color Theme</div>
              <div className={styles.scrollRow}>
                {Object.values(colorThemes).map((theme) => (
                  <div
                    key={theme.id}
                    ref={localColorId === theme.id ? activeColorRef : null}
                    className={`${styles.colorOption} ${
                      localColorId === theme.id ? styles.active : ""
                    }`}
                    onClick={() => setLocalColorId(theme.id)}
                    title={theme.name}
                  >
                    <div className={styles.miniPreview}>
                      <div 
                        className={styles.miniSidebar} 
                        style={{ background: theme.colors.bgSurface }} 
                      />
                      <div 
                        className={styles.miniContent} 
                        style={{ background: theme.colors.bgApp }}
                      >
                        <div 
                          className={styles.miniHeader} 
                          style={{ background: theme.colors.bgSurface }} 
                        />
                        <div 
                          className={styles.miniAccent} 
                          style={{ background: theme.colors.primary }} 
                        />
                      </div>
                    </div>
                    {localColorId === theme.id && (
                      <div style={{ 
                        position: 'absolute', 
                        inset: 0, 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        color: theme.id === 'dark' || theme.id === 'midnight' ? 'white' : 'black'
                      }}>
                        <Check size={16} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Fonts */}
            <div>
              <div className={styles.sectionTitle}>Typography</div>
              <div className={styles.scrollRow}>
                {Object.values(fontThemes).map((theme) => (
                  <div
                    key={theme.id}
                    ref={localFontId === theme.id ? activeFontRef : null}
                    className={`${styles.fontOption} ${
                      localFontId === theme.id ? styles.active : ""
                    }`}
                    onClick={() => setLocalFontId(theme.id)}
                    style={{ fontFamily: theme.fontFamily }}
                  >
                    <span>{theme.name}</span>
                    {localFontId === theme.id && <Check size={16} />}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className={styles.footer}>
          <button 
            className={`${styles.button} ${styles.buttonSecondary}`}
            onClick={onClose}
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
    </div>
  );
};
