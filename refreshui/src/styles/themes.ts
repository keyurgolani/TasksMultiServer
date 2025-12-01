export interface Theme {
  id: string;
  name: string;
  description: string;
  colors: {
    // Background colors
    bgApp: string;
    bgSurface: string;
    bgSurfaceHover: string;
    
    // Text colors
    textPrimary: string;
    textSecondary: string;
    textTertiary: string;
    
    // Accent colors
    primary: string;
    primaryDark: string;
    success: string;
    warning: string;
    error: string;
    info: string;
    
    // UI elements
    border: string;
    borderLight: string;
    shadow: string;
    
    // Scrollbar
    scrollbarThumb: string;
    scrollbarThumbHover: string;
    scrollbarThumbActive: string;
  };
}

export const themes: Record<string, Theme> = {
  light: {
    id: 'light',
    name: 'Light',
    description: 'Clean and bright',
    colors: {
      bgApp: '#f5f7fa',
      bgSurface: '#ffffff',
      bgSurfaceHover: '#f8f9fa',
      textPrimary: '#1a202c',
      textSecondary: '#4a5568',
      textTertiary: '#718096',
      primary: '#667eea',
      primaryDark: '#5568d3',
      success: '#2ed573',
      warning: '#ffa502',
      error: '#ff4757',
      info: '#3498db',
      border: 'rgba(0, 0, 0, 0.1)',
      borderLight: 'rgba(0, 0, 0, 0.05)',
      shadow: 'rgba(0, 0, 0, 0.1)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  dark: {
    id: 'dark',
    name: 'Dark',
    description: 'Vibrant dark mode',
    colors: {
      bgApp: '#0a0e1a',
      bgSurface: '#151b2e',
      bgSurfaceHover: '#1f2937',
      textPrimary: '#f0f4f8',
      textSecondary: '#c4cdd5',
      textTertiary: '#8b95a5',
      primary: '#7c3aed',
      primaryDark: '#6d28d9',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#3b82f6',
      border: 'rgba(255, 255, 255, 0.12)',
      borderLight: 'rgba(255, 255, 255, 0.06)',
      shadow: 'rgba(0, 0, 0, 0.4)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  ocean: {
    id: 'ocean',
    name: 'Ocean',
    description: 'Deep blue waters',
    colors: {
      bgApp: '#0a1929',
      bgSurface: '#132f4c',
      bgSurfaceHover: '#1e4976',
      textPrimary: '#e3f2fd',
      textSecondary: '#b3d9ff',
      textTertiary: '#7aa8d1',
      primary: '#00b4d8',
      primaryDark: '#0096c7',
      success: '#06ffa5',
      warning: '#ffb703',
      error: '#ff006e',
      info: '#48cae4',
      border: 'rgba(227, 242, 253, 0.12)',
      borderLight: 'rgba(227, 242, 253, 0.06)',
      shadow: 'rgba(0, 0, 0, 0.5)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  sunset: {
    id: 'sunset',
    name: 'Sunset',
    description: 'Warm evening glow',
    colors: {
      bgApp: '#1a0f2e',
      bgSurface: '#2d1b4e',
      bgSurfaceHover: '#3d2663',
      textPrimary: '#fef3e2',
      textSecondary: '#f4d9c6',
      textTertiary: '#d4a574',
      primary: '#ff6b35',
      primaryDark: '#e85d31',
      success: '#06ffa5',
      warning: '#ffd23f',
      error: '#ff006e',
      info: '#a78bfa',
      border: 'rgba(254, 243, 226, 0.12)',
      borderLight: 'rgba(254, 243, 226, 0.06)',
      shadow: 'rgba(0, 0, 0, 0.5)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  forest: {
    id: 'forest',
    name: 'Forest',
    description: 'Natural earth tones',
    colors: {
      bgApp: '#0f1a0f',
      bgSurface: '#1a2e1a',
      bgSurfaceHover: '#243d24',
      textPrimary: '#e8f5e8',
      textSecondary: '#c1e1c1',
      textTertiary: '#8fbc8f',
      primary: '#52b788',
      primaryDark: '#40916c',
      success: '#95d5b2',
      warning: '#ffb703',
      error: '#d62828',
      info: '#4cc9f0',
      border: 'rgba(232, 245, 232, 0.12)',
      borderLight: 'rgba(232, 245, 232, 0.06)',
      shadow: 'rgba(0, 0, 0, 0.5)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  lavender: {
    id: 'lavender',
    name: 'Lavender',
    description: 'Soft purple dream',
    colors: {
      bgApp: '#faf5ff',
      bgSurface: '#f3e8ff',
      bgSurfaceHover: '#e9d5ff',
      textPrimary: '#3b0764',
      textSecondary: '#581c87',
      textTertiary: '#7e22ce',
      primary: '#a855f7',
      primaryDark: '#9333ea',
      success: '#22c55e',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#3b82f6',
      border: 'rgba(59, 7, 100, 0.12)',
      borderLight: 'rgba(59, 7, 100, 0.06)',
      shadow: 'rgba(168, 85, 247, 0.15)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  coral: {
    id: 'coral',
    name: 'Coral',
    description: 'Warm coral reef',
    colors: {
      bgApp: '#fff5f5',
      bgSurface: '#ffe4e6',
      bgSurfaceHover: '#fecdd3',
      textPrimary: '#7f1d1d',
      textSecondary: '#991b1b',
      textTertiary: '#b91c1c',
      primary: '#fb7185',
      primaryDark: '#f43f5e',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#dc2626',
      info: '#06b6d4',
      border: 'rgba(127, 29, 29, 0.12)',
      borderLight: 'rgba(127, 29, 29, 0.06)',
      shadow: 'rgba(251, 113, 133, 0.15)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  nord: {
    id: 'nord',
    name: 'Nord',
    description: 'Arctic, north-bluish',
    colors: {
      bgApp: '#2e3440',
      bgSurface: '#3b4252',
      bgSurfaceHover: '#434c5e',
      textPrimary: '#eceff4',
      textSecondary: '#d8dee9',
      textTertiary: '#a3be8c',
      primary: '#88c0d0',
      primaryDark: '#5e81ac',
      success: '#a3be8c',
      warning: '#ebcb8b',
      error: '#bf616a',
      info: '#81a1c1',
      border: 'rgba(216, 222, 233, 0.1)',
      borderLight: 'rgba(216, 222, 233, 0.05)',
      shadow: 'rgba(0, 0, 0, 0.3)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  dracula: {
    id: 'dracula',
    name: 'Dracula',
    description: 'Dark with vibrant colors',
    colors: {
      bgApp: '#282a36',
      bgSurface: '#44475a',
      bgSurfaceHover: '#6272a4',
      textPrimary: '#f8f8f2',
      textSecondary: '#e6e6e6',
      textTertiary: '#bd93f9',
      primary: '#bd93f9',
      primaryDark: '#9580d4',
      success: '#50fa7b',
      warning: '#f1fa8c',
      error: '#ff5555',
      info: '#8be9fd',
      border: 'rgba(248, 248, 242, 0.1)',
      borderLight: 'rgba(248, 248, 242, 0.05)',
      shadow: 'rgba(0, 0, 0, 0.4)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  monokai: {
    id: 'monokai',
    name: 'Monokai',
    description: 'Classic code editor',
    colors: {
      bgApp: '#272822',
      bgSurface: '#3e3d32',
      bgSurfaceHover: '#49483e',
      textPrimary: '#f8f8f2',
      textSecondary: '#cfcfc2',
      textTertiary: '#75715e',
      primary: '#66d9ef',
      primaryDark: '#4db8d8',
      success: '#a6e22e',
      warning: '#e6db74',
      error: '#f92672',
      info: '#66d9ef',
      border: 'rgba(248, 248, 242, 0.1)',
      borderLight: 'rgba(248, 248, 242, 0.05)',
      shadow: 'rgba(0, 0, 0, 0.4)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  solarized: {
    id: 'solarized',
    name: 'Solarized',
    description: 'Precision colors',
    colors: {
      bgApp: '#002b36',
      bgSurface: '#073642',
      bgSurfaceHover: '#0f4552',
      textPrimary: '#fdf6e3',
      textSecondary: '#eee8d5',
      textTertiary: '#93a1a1',
      primary: '#268bd2',
      primaryDark: '#1e6fa8',
      success: '#859900',
      warning: '#b58900',
      error: '#dc322f',
      info: '#2aa198',
      border: 'rgba(253, 246, 227, 0.1)',
      borderLight: 'rgba(253, 246, 227, 0.05)',
      shadow: 'rgba(0, 0, 0, 0.4)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  gruvbox: {
    id: 'gruvbox',
    name: 'Gruvbox',
    description: 'Retro groove',
    colors: {
      bgApp: '#282828',
      bgSurface: '#3c3836',
      bgSurfaceHover: '#504945',
      textPrimary: '#ebdbb2',
      textSecondary: '#d5c4a1',
      textTertiary: '#a89984',
      primary: '#83a598',
      primaryDark: '#689d6a',
      success: '#b8bb26',
      warning: '#fabd2f',
      error: '#fb4934',
      info: '#83a598',
      border: 'rgba(235, 219, 178, 0.1)',
      borderLight: 'rgba(235, 219, 178, 0.05)',
      shadow: 'rgba(0, 0, 0, 0.4)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  tokyoNight: {
    id: 'tokyoNight',
    name: 'Tokyo Night',
    description: 'Clean dark theme',
    colors: {
      bgApp: '#1a1b26',
      bgSurface: '#24283b',
      bgSurfaceHover: '#2f3549',
      textPrimary: '#c0caf5',
      textSecondary: '#a9b1d6',
      textTertiary: '#565f89',
      primary: '#7aa2f7',
      primaryDark: '#5a7ec7',
      success: '#9ece6a',
      warning: '#e0af68',
      error: '#f7768e',
      info: '#7dcfff',
      border: 'rgba(192, 202, 245, 0.1)',
      borderLight: 'rgba(192, 202, 245, 0.05)',
      shadow: 'rgba(0, 0, 0, 0.4)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  catppuccin: {
    id: 'catppuccin',
    name: 'Catppuccin',
    description: 'Soothing pastel',
    colors: {
      bgApp: '#1e1e2e',
      bgSurface: '#313244',
      bgSurfaceHover: '#45475a',
      textPrimary: '#cdd6f4',
      textSecondary: '#bac2de',
      textTertiary: '#a6adc8',
      primary: '#89b4fa',
      primaryDark: '#6a8ec7',
      success: '#a6e3a1',
      warning: '#f9e2af',
      error: '#f38ba8',
      info: '#89dceb',
      border: 'rgba(205, 214, 244, 0.1)',
      borderLight: 'rgba(205, 214, 244, 0.05)',
      shadow: 'rgba(0, 0, 0, 0.4)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  oneDark: {
    id: 'oneDark',
    name: 'One Dark',
    description: "Atom's iconic theme",
    colors: {
      bgApp: '#282c34',
      bgSurface: '#2c313a',
      bgSurfaceHover: '#3e4451',
      textPrimary: '#abb2bf',
      textSecondary: '#9da5b4',
      textTertiary: '#5c6370',
      primary: '#61afef',
      primaryDark: '#4a8ec7',
      success: '#98c379',
      warning: '#e5c07b',
      error: '#e06c75',
      info: '#56b6c2',
      border: 'rgba(171, 178, 191, 0.1)',
      borderLight: 'rgba(171, 178, 191, 0.05)',
      shadow: 'rgba(0, 0, 0, 0.4)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  material: {
    id: 'material',
    name: 'Material',
    description: 'Google Material Design',
    colors: {
      bgApp: '#263238',
      bgSurface: '#37474f',
      bgSurfaceHover: '#455a64',
      textPrimary: '#eceff1',
      textSecondary: '#cfd8dc',
      textTertiary: '#90a4ae',
      primary: '#80cbc4',
      primaryDark: '#5fa39a',
      success: '#c3e88d',
      warning: '#ffcb6b',
      error: '#f07178',
      info: '#89ddff',
      border: 'rgba(236, 239, 241, 0.1)',
      borderLight: 'rgba(236, 239, 241, 0.05)',
      shadow: 'rgba(0, 0, 0, 0.4)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  synthwave: {
    id: 'synthwave',
    name: 'Synthwave',
    description: 'Outrun cyberpunk',
    colors: {
      bgApp: '#241b2f',
      bgSurface: '#2a2139',
      bgSurfaceHover: '#34294f',
      textPrimary: '#f8f8f2',
      textSecondary: '#e0d9f0',
      textTertiary: '#b4a5d8',
      primary: '#ff7edb',
      primaryDark: '#d65fb8',
      success: '#72f1b8',
      warning: '#fede5d',
      error: '#fe4450',
      info: '#36f9f6',
      border: 'rgba(248, 248, 242, 0.1)',
      borderLight: 'rgba(248, 248, 242, 0.05)',
      shadow: 'rgba(0, 0, 0, 0.5)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
  rosePine: {
    id: 'rosePine',
    name: 'Rosé Pine',
    description: 'Natural pine vibes',
    colors: {
      bgApp: '#191724',
      bgSurface: '#1f1d2e',
      bgSurfaceHover: '#26233a',
      textPrimary: '#e0def4',
      textSecondary: '#908caa',
      textTertiary: '#6e6a86',
      primary: '#c4a7e7',
      primaryDark: '#9c7ec0',
      success: '#9ccfd8',
      warning: '#f6c177',
      error: '#eb6f92',
      info: '#31748f',
      border: 'rgba(224, 222, 244, 0.1)',
      borderLight: 'rgba(224, 222, 244, 0.05)',
      shadow: 'rgba(0, 0, 0, 0.4)',
      scrollbarThumb: 'rgba(107, 115, 255, 0.4)',
      scrollbarThumbHover: 'rgba(107, 115, 255, 0.6)',
      scrollbarThumbActive: 'rgba(107, 115, 255, 0.8)',
    },
  },
};

export const applyTheme = (theme: Theme) => {
  const root = document.documentElement;
  
  // Apply all color variables
  root.style.setProperty('--bg-app', theme.colors.bgApp);
  root.style.setProperty('--bg-surface', theme.colors.bgSurface);
  root.style.setProperty('--bg-surface-hover', theme.colors.bgSurfaceHover);
  root.style.setProperty('--text-primary', theme.colors.textPrimary);
  root.style.setProperty('--text-secondary', theme.colors.textSecondary);
  root.style.setProperty('--text-tertiary', theme.colors.textTertiary);
  root.style.setProperty('--primary', theme.colors.primary);
  root.style.setProperty('--primary-dark', theme.colors.primaryDark);
  root.style.setProperty('--success', theme.colors.success);
  root.style.setProperty('--warning', theme.colors.warning);
  root.style.setProperty('--error', theme.colors.error);
  root.style.setProperty('--info', theme.colors.info);
  root.style.setProperty('--border', theme.colors.border);
  root.style.setProperty('--border-light', theme.colors.borderLight);
  root.style.setProperty('--shadow', theme.colors.shadow);
  
  // Set data-theme attribute for compatibility
  // Light themes: light, lavender, coral
  const lightThemes = ['light', 'lavender', 'coral'];
  root.setAttribute('data-theme', lightThemes.includes(theme.id) ? 'light' : 'dark');
};

export const saveTheme = (themeId: string) => {
  localStorage.setItem('preferred-theme', themeId);
};

export const loadSavedTheme = (): string => {
  const saved = localStorage.getItem('preferred-theme');
  if (saved) return saved;
  
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  
  return 'light';
};

export const getTheme = (themeId: string): Theme => {
  return themes[themeId] || themes.light;
};
