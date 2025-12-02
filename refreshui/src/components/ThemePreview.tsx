import React from 'react';
import { 
  type ColorTheme, 
  type FontTheme, 
  type EffectSettings,
  getThemeCssVariables 
} from '../styles/themes';
import styles from './ThemePreview.module.css';

interface ThemePreviewProps {
  colorTheme: ColorTheme;
  fontTheme: FontTheme;
  effectSettings: EffectSettings;
}

export const ThemePreview: React.FC<ThemePreviewProps> = ({
  colorTheme,
  fontTheme,
  effectSettings
}) => {
  const cssVars = getThemeCssVariables(colorTheme, fontTheme, effectSettings) as React.CSSProperties;

  return (
    <div className={styles.previewContainer} style={cssVars}>
      {/* Header Skeleton */}
      <div className={styles.header}>
        <div className={styles.logoSkeleton} />
        <div className={styles.searchSkeleton} />
        <div className={styles.avatarSkeleton} />
      </div>

      <div className={styles.content}>
        {/* Sidebar Skeleton */}
        <div className={styles.sidebar}>
          <div className={styles.sidebarItem} style={{ width: '80%' }} />
          <div className={styles.sidebarItem} style={{ width: '60%' }} />
          <div className={styles.sidebarItem} style={{ width: '70%' }} />
          <div className={styles.sidebarItem} style={{ width: '50%' }} />
        </div>

        {/* Main Content Skeleton (Tasks View) */}
        <div className={styles.main}>
          <div className={styles.pageTitleSkeleton} />
          
          {/* Task Card 1 */}
          <div className={styles.card}>
            <div className={styles.cardContent}>
              <div className={styles.row}>
                <div className={styles.cardTitle}>Design System Update</div>
                <div className={styles.indicator} />
              </div>
              <div className={styles.cardLine} />
              <div className={styles.cardLine} style={{ width: '40%' }} />
            </div>
          </div>

          {/* Task Card 2 */}
          <div className={styles.card}>
            <div className={styles.cardContent}>
              <div className={styles.row}>
                <div className={styles.cardTitle}>Client Meeting</div>
                <div className={styles.indicator} style={{ backgroundColor: 'var(--warning)', boxShadow: '0 0 10px var(--glow-warning)' }} />
              </div>
              <div className={styles.cardLine} style={{ width: '80%' }} />
            </div>
          </div>

          {/* Task Card 3 */}
          <div className={styles.card}>
            <div className={styles.cardContent}>
              <div className={styles.row}>
                <div className={styles.cardTitle}>Bug Fixes</div>
                <div className={styles.indicator} style={{ backgroundColor: 'var(--error)', boxShadow: '0 0 10px var(--glow-danger)' }} />
              </div>
              <div className={styles.cardLine} style={{ width: '50%' }} />
            </div>
          </div>
        </div>
      </div>

      {/* FAB Skeleton */}
      <div className={styles.fabSkeleton} />
    </div>
  );
};
