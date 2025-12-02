export type ThemeCategory = 'glass' | 'tactile' | 'bold' | 'minimal' | 'vibrant' | 'futuristic';
export type VisualIntensity = 'subtle' | 'moderate' | 'bold';
export type BorderRadius = 'sharp' | 'rounded' | 'pill';
export type ShadowDepth = 'none' | 'subtle' | 'moderate' | 'dramatic';

export interface ThemeConfig {
  intensity: VisualIntensity;
  radius: BorderRadius;
  shadow: ShadowDepth;
}

export interface Theme {
  id: string;
  name: string;
  description: string;
  category?: ThemeCategory;
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

    // Glassmorphism
    glassBg: string;
    glassBorder: string;
    glassShadow: string;
    glassBlur: string;

    // Glow effects
    glowPrimary: string;
    glowSuccess: string;
    glowWarning: string;
    glowDanger: string;
  };
  config?: ThemeConfig;
}

export const themes: Record<string, Theme> = {
  light: {
    id: 'light',
    category: 'minimal',
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

      // Glassmorphism - Light theme
      glassBg: 'rgba(255, 255, 255, 0.85)',
      glassBorder: 'rgba(0, 0, 0, 0.1)',
      glassShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
      glassBlur: 'blur(10px)',

      // Glow effects - Light theme
      glowPrimary: '0 4px 12px rgba(107, 115, 255, 0.3)',
      glowSuccess: '0 4px 12px rgba(46, 213, 115, 0.3)',
      glowWarning: '0 4px 12px rgba(255, 165, 2, 0.3)',
      glowDanger: '0 4px 12px rgba(255, 71, 87, 0.3)',
    },
  },
  dark: {
    id: 'dark',
    category: 'minimal',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  ocean: {
    id: 'ocean',
    category: 'vibrant',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  sunset: {
    id: 'sunset',
    category: 'vibrant',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  forest: {
    id: 'forest',
    category: 'vibrant',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  lavender: {
    id: 'lavender',
    category: 'vibrant',
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
      // Glassmorphism - Light theme
      glassBg: 'rgba(255, 255, 255, 0.6)',
      glassBorder: 'rgba(59, 7, 100, 0.1)',
      glassShadow: '0 8px 32px 0 rgba(168, 85, 247, 0.15)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  coral: {
    id: 'coral',
    category: 'vibrant',
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
      // Glassmorphism - Light theme
      glassBg: 'rgba(255, 255, 255, 0.6)',
      glassBorder: 'rgba(127, 29, 29, 0.1)',
      glassShadow: '0 8px 32px 0 rgba(251, 113, 133, 0.15)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  nord: {
    id: 'nord',
    category: 'minimal',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  dracula: {
    id: 'dracula',
    category: 'minimal',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  monokai: {
    id: 'monokai',
    category: 'minimal',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  solarized: {
    id: 'solarized',
    category: 'minimal',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  gruvbox: {
    id: 'gruvbox',
    category: 'minimal',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  tokyoNight: {
    id: 'tokyoNight',
    category: 'futuristic',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  catppuccin: {
    id: 'catppuccin',
    category: 'minimal',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  oneDark: {
    id: 'oneDark',
    category: 'minimal',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  material: {
    id: 'material',
    category: 'minimal',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  synthwave: {
    id: 'synthwave',
    category: 'futuristic',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  rosePine: {
    id: 'rosePine',
    category: 'minimal',
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
      // Glassmorphism - Dark theme
      glassBg: 'rgba(30, 33, 40, 0.75)',
      glassBorder: 'rgba(255, 255, 255, 0.08)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(12px)',

      // Glow effects - Dark theme
      glowPrimary: '0 0 20px rgba(107, 115, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  glassmorphism: {
    id: 'glassmorphism',
    name: 'Glassmorphism',
    description: 'Frosted glass effects',
    category: 'glass',
    config: { intensity: 'bold', radius: 'rounded', shadow: 'moderate' },
    colors: {
      bgApp: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      bgSurface: 'rgba(255, 255, 255, 0.1)',
      bgSurfaceHover: 'rgba(255, 255, 255, 0.2)',
      textPrimary: '#ffffff',
      textSecondary: 'rgba(255, 255, 255, 0.8)',
      textTertiary: 'rgba(255, 255, 255, 0.6)',
      primary: '#ffffff',
      primaryDark: '#e0e0e0',
      success: '#2ed573',
      warning: '#ffa502',
      error: '#ff4757',
      info: '#3498db',
      border: 'rgba(255, 255, 255, 0.2)',
      borderLight: 'rgba(255, 255, 255, 0.1)',
      shadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
      scrollbarThumb: 'rgba(255, 255, 255, 0.3)',
      scrollbarThumbHover: 'rgba(255, 255, 255, 0.5)',
      scrollbarThumbActive: 'rgba(255, 255, 255, 0.7)',
      glassBg: 'rgba(255, 255, 255, 0.1)',
      glassBorder: 'rgba(255, 255, 255, 0.2)',
      glassShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
      glassBlur: 'blur(20px)',
      glowPrimary: '0 0 20px rgba(255, 255, 255, 0.4)',
      glowSuccess: '0 0 15px rgba(46, 213, 115, 0.4)',
      glowWarning: '0 0 15px rgba(255, 165, 2, 0.4)',
      glowDanger: '0 0 15px rgba(255, 71, 87, 0.4)',
    },
  },
  frost: {
    id: 'frost',
    name: 'Frost UI',
    description: 'Subtle transparency',
    category: 'glass',
    config: { intensity: 'subtle', radius: 'rounded', shadow: 'subtle' },
    colors: {
      bgApp: '#f0f2f5',
      bgSurface: 'rgba(255, 255, 255, 0.7)',
      bgSurfaceHover: 'rgba(255, 255, 255, 0.8)',
      textPrimary: '#1a202c',
      textSecondary: '#4a5568',
      textTertiary: '#718096',
      primary: '#3182ce',
      primaryDark: '#2c5282',
      success: '#38a169',
      warning: '#d69e2e',
      error: '#e53e3e',
      info: '#3182ce',
      border: 'rgba(255, 255, 255, 0.5)',
      borderLight: 'rgba(255, 255, 255, 0.3)',
      shadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      scrollbarThumb: 'rgba(49, 130, 206, 0.4)',
      scrollbarThumbHover: 'rgba(49, 130, 206, 0.6)',
      scrollbarThumbActive: 'rgba(49, 130, 206, 0.8)',
      glassBg: 'rgba(255, 255, 255, 0.7)',
      glassBorder: 'rgba(255, 255, 255, 0.5)',
      glassShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      glassBlur: 'blur(10px)',
      glowPrimary: '0 4px 12px rgba(49, 130, 206, 0.3)',
      glowSuccess: '0 4px 12px rgba(56, 161, 105, 0.3)',
      glowWarning: '0 4px 12px rgba(214, 158, 46, 0.3)',
      glowDanger: '0 4px 12px rgba(229, 62, 62, 0.3)',
    },
  },
  neumorphismLight: {
    id: 'neumorphismLight',
    name: 'Neumorphism (Light)',
    description: 'Soft tactile feel',
    category: 'tactile',
    config: { intensity: 'moderate', radius: 'rounded', shadow: 'moderate' },
    colors: {
      bgApp: '#e0e5ec',
      bgSurface: '#e0e5ec',
      bgSurfaceHover: '#e0e5ec', // Neumorphism relies on shadows, not bg color changes
      textPrimary: '#4a5568',
      textSecondary: '#718096',
      textTertiary: '#a0aec0',
      primary: '#667eea',
      primaryDark: '#5a67d8',
      success: '#48bb78',
      warning: '#ed8936',
      error: '#f56565',
      info: '#4299e1',
      border: 'transparent',
      borderLight: 'transparent',
      shadow: '9px 9px 16px rgb(163,177,198,0.6), -9px -9px 16px rgba(255,255,255, 0.5)',
      scrollbarThumb: '#a3b1c6',
      scrollbarThumbHover: '#8d9db6',
      scrollbarThumbActive: '#7a8ba6',
      glassBg: 'rgba(255, 255, 255, 0.5)',
      glassBorder: 'rgba(255, 255, 255, 0.2)',
      glassShadow: 'none',
      glassBlur: 'none',
      glowPrimary: 'none',
      glowSuccess: 'none',
      glowWarning: 'none',
      glowDanger: 'none',
    },
  },
  claymorphismLight: {
    id: 'claymorphismLight',
    name: 'Claymorphism',
    description: 'Playful 3D',
    category: 'tactile',
    config: { intensity: 'bold', radius: 'pill', shadow: 'dramatic' },
    colors: {
      bgApp: '#f0f4f8',
      bgSurface: '#ffffff',
      bgSurfaceHover: '#f8fafc',
      textPrimary: '#2d3748',
      textSecondary: '#4a5568',
      textTertiary: '#718096',
      primary: '#ff6b6b',
      primaryDark: '#ee5253',
      success: '#1dd1a1',
      warning: '#feca57',
      error: '#ff6b6b',
      info: '#54a0ff',
      border: 'rgba(255, 255, 255, 0.5)',
      borderLight: 'rgba(255, 255, 255, 0.3)',
      shadow: '8px 8px 16px rgba(163, 177, 198, 0.2), -8px -8px 16px rgba(255, 255, 255, 0.8), inset 2px 2px 4px rgba(255, 255, 255, 0.5), inset -2px -2px 4px rgba(0, 0, 0, 0.05)',
      scrollbarThumb: '#ff6b6b',
      scrollbarThumbHover: '#ee5253',
      scrollbarThumbActive: '#d63031',
      glassBg: 'rgba(255, 255, 255, 0.8)',
      glassBorder: 'rgba(255, 255, 255, 0.5)',
      glassShadow: '8px 8px 16px rgba(0,0,0,0.1)',
      glassBlur: 'blur(10px)',
      glowPrimary: '0 10px 20px rgba(255, 107, 107, 0.3)',
      glowSuccess: '0 10px 20px rgba(29, 209, 161, 0.3)',
      glowWarning: '0 10px 20px rgba(254, 202, 87, 0.3)',
      glowDanger: '0 10px 20px rgba(255, 107, 107, 0.3)',
    },
  },
  neoBrutalism: {
    id: 'neoBrutalism',
    name: 'Neo-Brutalism',
    description: 'Bold and raw',
    category: 'bold',
    config: { intensity: 'bold', radius: 'sharp', shadow: 'dramatic' },
    colors: {
      bgApp: '#fffdf5',
      bgSurface: '#ffffff',
      bgSurfaceHover: '#e2e8f0',
      textPrimary: '#000000',
      textSecondary: '#1a202c',
      textTertiary: '#2d3748',
      primary: '#8b5cf6',
      primaryDark: '#7c3aed',
      success: '#4ade80',
      warning: '#facc15',
      error: '#f87171',
      info: '#60a5fa',
      border: '#000000',
      borderLight: '#000000',
      shadow: '4px 4px 0px #000000',
      scrollbarThumb: '#000000',
      scrollbarThumbHover: '#333333',
      scrollbarThumbActive: '#000000',
      glassBg: '#ffffff',
      glassBorder: '#000000',
      glassShadow: '4px 4px 0px #000000',
      glassBlur: 'none',
      glowPrimary: 'none',
      glowSuccess: 'none',
      glowWarning: 'none',
      glowDanger: 'none',
    },
  },
  aurora: {
    id: 'aurora',
    name: 'Aurora',
    description: 'Glowing light streaks',
    category: 'vibrant',
    config: { intensity: 'moderate', radius: 'rounded', shadow: 'moderate' },
    colors: {
      bgApp: '#0f172a',
      bgSurface: 'rgba(30, 41, 59, 0.7)',
      bgSurfaceHover: 'rgba(51, 65, 85, 0.7)',
      textPrimary: '#f8fafc',
      textSecondary: '#cbd5e1',
      textTertiary: '#94a3b8',
      primary: '#38bdf8',
      primaryDark: '#0ea5e9',
      success: '#4ade80',
      warning: '#facc15',
      error: '#f87171',
      info: '#818cf8',
      border: 'rgba(255, 255, 255, 0.1)',
      borderLight: 'rgba(255, 255, 255, 0.05)',
      shadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
      scrollbarThumb: 'rgba(56, 189, 248, 0.4)',
      scrollbarThumbHover: 'rgba(56, 189, 248, 0.6)',
      scrollbarThumbActive: 'rgba(56, 189, 248, 0.8)',
      glassBg: 'rgba(30, 41, 59, 0.7)',
      glassBorder: 'rgba(255, 255, 255, 0.1)',
      glassShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      glassBlur: 'blur(16px)',
      glowPrimary: '0 0 30px rgba(56, 189, 248, 0.5)',
      glowSuccess: '0 0 20px rgba(74, 222, 128, 0.5)',
      glowWarning: '0 0 20px rgba(250, 204, 21, 0.5)',
      glowDanger: '0 0 20px rgba(248, 113, 113, 0.5)',
    },
  },
  cyber: {
    id: 'cyber',
    name: 'Cyberpunk',
    description: 'High tech low life',
    category: 'futuristic',
    config: { intensity: 'bold', radius: 'sharp', shadow: 'dramatic' },
    colors: {
      bgApp: '#000000',
      bgSurface: '#121212',
      bgSurfaceHover: '#1e1e1e',
      textPrimary: '#00ff41',
      textSecondary: '#008f11',
      textTertiary: '#003b00',
      primary: '#fdf500',
      primaryDark: '#d1cb00',
      success: '#00ff41',
      warning: '#fdf500',
      error: '#ff003c',
      info: '#00f0ff',
      border: '#00ff41',
      borderLight: '#008f11',
      shadow: '0 0 10px #00ff41',
      scrollbarThumb: '#00ff41',
      scrollbarThumbHover: '#008f11',
      scrollbarThumbActive: '#003b00',
      glassBg: 'rgba(0, 0, 0, 0.8)',
      glassBorder: '#00ff41',
      glassShadow: '0 0 15px #00ff41',
      glassBlur: 'blur(2px)',
      glowPrimary: '0 0 20px #fdf500',
      glowSuccess: '0 0 20px #00ff41',
      glowWarning: '0 0 20px #fdf500',
      glowDanger: '0 0 20px #ff003c',
    },
  },
};

export const fonts = {
  inter: { name: 'Inter', value: '"Inter", sans-serif' },
  roboto: { name: 'Roboto', value: '"Roboto", sans-serif' },
  quicksand: { name: 'Quicksand', value: '"Quicksand", sans-serif' },
  fira: { name: 'Fira Code', value: '"Fira Code", monospace' },
  space: { name: 'Space Grotesk', value: '"Space Grotesk", sans-serif' },
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
  
  // Apply glassmorphism variables
  root.style.setProperty('--glass-bg', theme.colors.glassBg);
  root.style.setProperty('--glass-border', theme.colors.glassBorder);
  root.style.setProperty('--glass-shadow', theme.colors.glassShadow);
  root.style.setProperty('--glass-blur', theme.colors.glassBlur);
  
  // Apply glow effect variables
  root.style.setProperty('--glow-primary', theme.colors.glowPrimary);
  root.style.setProperty('--glow-success', theme.colors.glowSuccess);
  root.style.setProperty('--glow-warning', theme.colors.glowWarning);
  root.style.setProperty('--glow-danger', theme.colors.glowDanger);

  // Apply config
  const config = theme.config || { intensity: 'moderate', radius: 'rounded', shadow: 'moderate' };
  root.setAttribute('data-intensity', config.intensity);
  root.setAttribute('data-radius', config.radius);
  root.setAttribute('data-shadow', config.shadow);
  
  // Set data-theme attribute for compatibility
  // Light themes: light, lavender, coral, frost, neumorphismLight
  const lightThemes = ['light', 'lavender', 'coral', 'frost', 'neumorphismLight', 'claymorphismLight', 'minimalLight'];
  root.setAttribute('data-theme', lightThemes.includes(theme.id) ? 'light' : 'dark');
};

export const applyFont = (fontValue: string) => {
  document.documentElement.style.setProperty('--font-default', fontValue);
};

export const saveTheme = (themeId: string) => {
  localStorage.setItem('preferred-theme', themeId);
};

export const saveFont = (fontKey: string) => {
  localStorage.setItem('preferred-font', fontKey);
};

export const loadSavedTheme = (): string => {
  const saved = localStorage.getItem('preferred-theme');
  if (saved) return saved;
  
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  
  return 'light';
};

export const loadSavedFont = (): string => {
  return localStorage.getItem('preferred-font') || 'inter';
};

export const getTheme = (themeId: string): Theme => {
  return themes[themeId] || themes.light;
};
