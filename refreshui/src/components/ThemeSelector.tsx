import React, { useState } from 'react';
import { ChevronDown, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactDOM from 'react-dom';
import { themes, type Theme, fonts, applyFont, saveFont, loadSavedFont } from '../styles/themes';
import styles from './ThemeSelector.module.css';

interface ThemeSelectorProps {
  currentTheme: string;
  onThemeChange: (theme: string) => void;
}

export const ThemeSelector: React.FC<ThemeSelectorProps> = ({ currentTheme, onThemeChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentFont, setCurrentFont] = useState(() => loadSavedFont());

  const currentThemeData = themes[currentTheme] || themes.light;
  const themeList = Object.values(themes);
  const fontList = Object.entries(fonts);

  const handleFontChange = (fontKey: string, fontValue: string) => {
    setCurrentFont(fontKey);
    applyFont(fontValue);
    saveFont(fontKey);
  };

  // Helper to render the skeleton UI
  const renderPreview = (theme: Theme, isMini: boolean) => (
    <div 
      className={isMini ? styles.miniPreview : styles.themePreviewLarge}
      style={{ 
        backgroundColor: theme.colors.bgApp,
        borderColor: theme.colors.border 
      }}
    >
      {/* Sidebar */}
      <div 
        className={styles.previewSidebar} 
        style={{ 
          backgroundColor: theme.colors.bgSurface,
          borderRight: `1px solid ${theme.colors.border}`
        }} 
      />
      
      {/* Header */}
      <div 
        className={styles.previewHeader} 
        style={{ 
          backgroundColor: theme.colors.bgSurface,
          borderBottom: `1px solid ${theme.colors.border}`
        }} 
      />

      {/* Content - Task Cards */}
      <div className={styles.previewContent}>
        <div 
          className={styles.previewCard} 
          style={{ 
            backgroundColor: theme.colors.bgSurface,
            borderColor: theme.colors.border
          }} 
        />
        <div 
          className={styles.previewCard} 
          style={{ 
            backgroundColor: theme.colors.bgSurface,
            borderColor: theme.colors.border,
            opacity: 0.6
          }} 
        />
      </div>

      {/* FAB */}
      <div 
        className={styles.previewFab} 
        style={{ backgroundColor: theme.colors.primary }} 
      />
    </div>
  );

  return (
    <>
      <div className={styles.container}>
        <button
          className={styles.trigger}
          onClick={() => setIsOpen(!isOpen)}
        >
          <div className={styles.currentTheme}>
            {renderPreview(currentThemeData, true)}
            <span>{currentThemeData.name}</span>
          </div>
          <ChevronDown size={16} className={isOpen ? styles.iconRotated : ''} />
        </button>
      </div>

      {ReactDOM.createPortal(
        <AnimatePresence>
          {isOpen && (
            <>
              <motion.div 
                className={styles.backdrop}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2, ease: 'easeInOut' }}
                onClick={() => setIsOpen(false)}
              />
              <motion.div
                className={styles.popup}
                initial={{ opacity: 0, scale: 0.92, x: "-50%", y: "-50%" }}
                animate={{ opacity: 1, scale: 1, x: "-50%", y: "-50%" }}
                exit={{ opacity: 0, scale: 0.92, x: "-50%", y: "-50%" }}
                transition={{ 
                  type: 'spring',
                  damping: 25,
                  stiffness: 300,
                  mass: 0.8
                }}
              >
                <div className={styles.popupHeader}>
                  <h3>Appearance</h3>
                  <button className={styles.closeButton} onClick={() => setIsOpen(false)}>
                    ×
                  </button>
                </div>

                <div className={styles.sectionTitle}>Theme</div>
                <div className={styles.themeGrid}>
                  {themeList.map((theme, index) => (
                    <motion.button
                      key={theme.id}
                      className={`${styles.themeOption} ${currentTheme === theme.id ? styles.active : ''}`}
                      onClick={() => {
                        onThemeChange(theme.id);
                      }}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ 
                        delay: index * 0.05,
                        duration: 0.3,
                        ease: 'easeOut'
                      }}
                    >
                      {renderPreview(theme, false)}
                      <div className={styles.themeInfo}>
                        <div className={styles.themeName}>{theme.name}</div>
                        <div className={styles.themeDescription}>{theme.description}</div>
                      </div>
                      {currentTheme === theme.id && (
                        <motion.div 
                          className={styles.activeBadge}
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          transition={{ 
                            type: 'spring',
                            stiffness: 500,
                            damping: 25
                          }}
                        >
                          <Check size={12} />
                        </motion.div>
                      )}
                    </motion.button>
                  ))}
                </div>

                <div className={styles.sectionTitle}>Font</div>
                <div className={styles.fontGrid}>
                  {fontList.map(([key, font]) => (
                    <button
                      key={key}
                      className={`${styles.fontOption} ${currentFont === key ? styles.active : ''}`}
                      onClick={() => handleFontChange(key, font.value)}
                      style={{ fontFamily: font.value }}
                    >
                      <span className={styles.fontName}>{font.name}</span>
                      <span className={styles.fontPreview}>Aa</span>
                      {currentFont === key && <Check size={16} className={styles.checkIcon} />}
                    </button>
                  ))}
                </div>

              </motion.div>
            </>
          )}
        </AnimatePresence>,
        document.body
      )}
    </>
  );
};
