import React, { createContext, useContext, useEffect, useState } from 'react';
import { 
  type ColorTheme, 
  type FontTheme, 
  type EffectSettings,
  applyTheme, 
  loadSavedTheme, 
  saveTheme, 
  colorThemes,
  fontThemes,
  defaultEffectSettings
} from '../styles/themes';

interface ThemeContextType {
  activeColorTheme: ColorTheme;
  activeFontTheme: FontTheme;
  activeEffectSettings: EffectSettings;
  setColorTheme: (id: string) => void;
  setFontTheme: (id: string) => void;
  setEffectSettings: (settings: EffectSettings) => void;
  updateEffectSetting: (key: keyof EffectSettings, value: number) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Initialize state from local storage or defaults
  const saved = loadSavedTheme();
  
  const [colorId, setColorId] = useState<string>(saved?.colorId || 'light');
  const [fontId, setFontId] = useState<string>(saved?.fontId || 'inter');
  const [effectSettings, setEffectSettingsState] = useState<EffectSettings>(saved?.effects || defaultEffectSettings);

  const activeColorTheme = colorThemes[colorId] || colorThemes.light;
  const activeFontTheme = fontThemes[fontId] || fontThemes.inter;

  useEffect(() => {
    applyTheme(activeColorTheme, activeFontTheme, effectSettings);
    saveTheme(colorId, fontId, effectSettings);
  }, [activeColorTheme, activeFontTheme, effectSettings, colorId, fontId]);

  const setColorTheme = (id: string) => {
    if (colorThemes[id]) {
      setColorId(id);
    }
  };

  const setFontTheme = (id: string) => {
    if (fontThemes[id]) {
      setFontId(id);
    }
  };

  const setEffectSettings = (settings: EffectSettings) => {
    setEffectSettingsState(settings);
  };

  const updateEffectSetting = (key: keyof EffectSettings, value: number) => {
    setEffectSettingsState(prev => ({
      ...prev,
      [key]: value
    }));
  };

  return (
    <ThemeContext.Provider 
      value={{ 
        activeColorTheme, 
        activeFontTheme, 
        activeEffectSettings: effectSettings,
        setColorTheme, 
        setFontTheme, 
        setEffectSettings,
        updateEffectSetting
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
