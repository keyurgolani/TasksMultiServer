import React, { createContext, useContext, useEffect, useState } from 'react';
import { 
  type Theme, 
  type ThemeConfig, 
  applyTheme, 
  getTheme, 
  loadSavedTheme, 
  saveTheme, 
  themes 
} from '../styles/themes';

interface ThemeContextType {
  currentTheme: Theme;
  setTheme: (themeId: string) => void;
  config: ThemeConfig;
  updateConfig: (config: Partial<ThemeConfig>) => void;
  resetConfig: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [themeId, setThemeId] = useState<string>(loadSavedTheme());
  const [customConfig, setCustomConfig] = useState<Partial<ThemeConfig>>({});

  const currentTheme = getTheme(themeId);

  // Merge theme default config with custom config
  const activeConfig: ThemeConfig = React.useMemo(() => ({
    intensity: customConfig.intensity || currentTheme.config?.intensity || 'moderate',
    radius: customConfig.radius || currentTheme.config?.radius || 'rounded',
    shadow: customConfig.shadow || currentTheme.config?.shadow || 'moderate',
  }), [customConfig, currentTheme.config]);

  useEffect(() => {
    // Apply theme with merged config
    const themeWithConfig = {
      ...currentTheme,
      config: activeConfig
    };
    applyTheme(themeWithConfig);
    saveTheme(themeId);
  }, [themeId, customConfig, currentTheme, activeConfig]);

  const handleSetTheme = (id: string) => {
    if (themes[id]) {
      setThemeId(id);
      // Optional: Reset custom config when switching themes? 
      // For now, let's keep it to allow "applying my preferences to any theme"
      // But maybe some themes don't support some configs.
      // Let's reset custom config to ensure we see the theme as intended first.
      setCustomConfig({});
    }
  };

  const updateConfig = (newConfig: Partial<ThemeConfig>) => {
    setCustomConfig(prev => ({ ...prev, ...newConfig }));
  };

  const resetConfig = () => {
    setCustomConfig({});
  };

  return (
    <ThemeContext.Provider 
      value={{ 
        currentTheme, 
        setTheme: handleSetTheme, 
        config: activeConfig, 
        updateConfig,
        resetConfig
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
