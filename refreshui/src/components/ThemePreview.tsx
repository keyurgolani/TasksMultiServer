import React from 'react';
import { type ColorTheme, type FontTheme, type EffectSettings, getThemeCssVariables } from '../styles/themes';
import styles from './ThemePreview.module.css';

interface ThemePreviewProps {
  colorTheme: ColorTheme;
  fontTheme: FontTheme;
  effectSettings: EffectSettings;
}

export const ThemePreview: React.FC<ThemePreviewProps> = ({
  colorTheme,
  fontTheme,
  effectSettings,
}) => {
  const cssVars = getThemeCssVariables(colorTheme, fontTheme, effectSettings);

  return (
    <div 
      className={styles.previewContainer}
      style={cssVars}
    >
      <div className={styles.header}>
        <div className={styles.title}>Tasks</div>
        <div className={styles.avatar} />
      </div>
      
      <div className={styles.content}>
        <div className={styles.sidebar}>
          <div className={styles.sidebarItem} />
          <div className={styles.sidebarItem} style={{ width: '70%' }} />
          <div className={styles.sidebarItem} style={{ width: '80%' }} />
        </div>
        
        <div className={styles.main}>
          <div className={styles.card}>
            <div className={styles.cardContent}>
              <div className={styles.row}>
                <span className={styles.cardTitle}>Task</span>
                <div className={styles.indicator} />
              </div>
              <div className={styles.cardLine} />
            </div>
          </div>
          
          <div className={styles.card}>
            <div className={styles.cardContent}>
              <div className={styles.cardLine} style={{ width: '40%' }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
