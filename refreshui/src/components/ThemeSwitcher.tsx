import React, { useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import { themes, type ThemeCategory, type VisualIntensity, type BorderRadius, type ShadowDepth } from '../styles/themes';

const categories: { id: ThemeCategory; label: string }[] = [
  { id: 'minimal', label: 'Minimal & Clean' },
  { id: 'glass', label: 'Glass & Transparency' },
  { id: 'tactile', label: 'Tactile & 3D' },
  { id: 'vibrant', label: 'Vibrant & Atmospheric' },
  { id: 'bold', label: 'Bold & Raw' },
  { id: 'futuristic', label: 'Futuristic & Tech' },
];

export const ThemeSwitcher: React.FC = () => {
  const { currentTheme, setTheme, config, updateConfig, resetConfig } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const [activeCategory, setActiveCategory] = useState<ThemeCategory>('minimal');

  const themeList = Object.values(themes);
  const filteredThemes = themeList.filter(t => (t.category || 'minimal') === activeCategory);

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 p-3 rounded-full bg-primary text-white shadow-lg z-50 hover:scale-105 transition-transform"
        style={{ backgroundColor: 'var(--primary)', color: 'var(--text-primary)' }}
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="5" />
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
        </svg>
      </button>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => setIsOpen(false)}>
      <div 
        className="bg-surface w-full max-w-4xl h-[80vh] rounded-xl shadow-2xl overflow-hidden flex flex-col"
        style={{ backgroundColor: 'var(--bg-surface)', color: 'var(--text-primary)' }}
        onClick={e => e.stopPropagation()}
      >
        <div className="p-6 border-b border-border flex justify-between items-center" style={{ borderColor: 'var(--border)' }}>
          <h2 className="text-2xl font-bold">Theme Studio</h2>
          <button onClick={() => setIsOpen(false)} className="p-2 hover:bg-surface-hover rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-hidden flex">
          {/* Sidebar - Categories */}
          <div className="w-64 border-r border-border overflow-y-auto p-4 space-y-2" style={{ borderColor: 'var(--border)' }}>
            <h3 className="text-sm font-semibold text-text-secondary mb-4 uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Categories</h3>
            {categories.map(cat => (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id)}
                className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                  activeCategory === cat.id 
                    ? 'bg-primary text-white' 
                    : 'hover:bg-surface-hover text-text-primary'
                }`}
                style={{ 
                  backgroundColor: activeCategory === cat.id ? 'var(--primary)' : 'transparent',
                  color: activeCategory === cat.id ? '#fff' : 'var(--text-primary)'
                }}
              >
                {cat.label}
              </button>
            ))}
          </div>

          {/* Main Content - Themes & Config */}
          <div className="flex-1 overflow-y-auto p-8">
            <div className="mb-8">
              <h3 className="text-xl font-semibold mb-4">Select Theme</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredThemes.map(theme => (
                  <button
                    key={theme.id}
                    onClick={() => setTheme(theme.id)}
                    className={`group relative p-4 rounded-xl border-2 transition-all text-left ${
                      currentTheme.id === theme.id 
                        ? 'border-primary ring-2 ring-primary/20' 
                        : 'border-border hover:border-primary/50'
                    }`}
                    style={{ 
                      borderColor: currentTheme.id === theme.id ? 'var(--primary)' : 'var(--border)',
                      backgroundColor: theme.colors.bgApp 
                    }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium" style={{ color: theme.colors.textPrimary }}>{theme.name}</span>
                      {currentTheme.id === theme.id && (
                        <span className="bg-primary text-white text-xs px-2 py-1 rounded-full" style={{ backgroundColor: theme.colors.primary }}>Active</span>
                      )}
                    </div>
                    <p className="text-sm opacity-80" style={{ color: theme.colors.textSecondary }}>{theme.description}</p>
                    
                    {/* Mini Preview */}
                    <div className="mt-4 flex gap-2">
                      <div className="w-6 h-6 rounded-full" style={{ backgroundColor: theme.colors.primary }}></div>
                      <div className="w-6 h-6 rounded-full" style={{ backgroundColor: theme.colors.success }}></div>
                      <div className="w-6 h-6 rounded-full" style={{ backgroundColor: theme.colors.error }}></div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="border-t border-border pt-8" style={{ borderColor: 'var(--border)' }}>
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-semibold">Customization</h3>
                <button 
                  onClick={resetConfig}
                  className="text-sm text-primary hover:underline"
                  style={{ color: 'var(--primary)' }}
                >
                  Reset to Defaults
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Intensity */}
                <div className="space-y-4">
                  <label className="block text-sm font-medium text-text-secondary" style={{ color: 'var(--text-secondary)' }}>Visual Intensity</label>
                  <div className="flex flex-col gap-2">
                    {(['subtle', 'moderate', 'bold'] as VisualIntensity[]).map(val => (
                      <label key={val} className="flex items-center gap-3 cursor-pointer p-2 rounded hover:bg-surface-hover">
                        <input 
                          type="radio" 
                          name="intensity" 
                          checked={config.intensity === val}
                          onChange={() => updateConfig({ intensity: val })}
                          className="accent-primary"
                        />
                        <span className="capitalize">{val}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Border Radius */}
                <div className="space-y-4">
                  <label className="block text-sm font-medium text-text-secondary" style={{ color: 'var(--text-secondary)' }}>Border Radius</label>
                  <div className="flex flex-col gap-2">
                    {(['sharp', 'rounded', 'pill'] as BorderRadius[]).map(val => (
                      <label key={val} className="flex items-center gap-3 cursor-pointer p-2 rounded hover:bg-surface-hover">
                        <input 
                          type="radio" 
                          name="radius" 
                          checked={config.radius === val}
                          onChange={() => updateConfig({ radius: val })}
                          className="accent-primary"
                        />
                        <span className="capitalize">{val}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Shadow Depth */}
                <div className="space-y-4">
                  <label className="block text-sm font-medium text-text-secondary" style={{ color: 'var(--text-secondary)' }}>Shadow Depth</label>
                  <div className="flex flex-col gap-2">
                    {(['none', 'subtle', 'moderate', 'dramatic'] as ShadowDepth[]).map(val => (
                      <label key={val} className="flex items-center gap-3 cursor-pointer p-2 rounded hover:bg-surface-hover">
                        <input 
                          type="radio" 
                          name="shadow" 
                          checked={config.shadow === val}
                          onChange={() => updateConfig({ shadow: val })}
                          className="accent-primary"
                        />
                        <span className="capitalize">{val}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
