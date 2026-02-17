export type ThemeCategory =
  | "glass"
  | "tactile"
  | "bold"
  | "minimal"
  | "vibrant"
  | "futuristic";

// --- Colors ---
export interface ColorTheme {
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

    // Scrollbar
    scrollbarThumb: string;
    scrollbarThumbHover: string;
    scrollbarThumbActive: string;

    // Base colors for effects (used to generate dynamic effects)
    glassColor: string; // Base color for glass background
    glassBorderColor: string; // Base color for glass border
    shadowColor: string; // Base color for shadows
  };
}

export const colorThemes: Record<string, ColorTheme> = {
  light: {
    id: "light",
    category: "minimal",
    name: "Light",
    description: "Clean and bright",
    colors: {
      bgApp: "#f5f7fa",
      bgSurface: "#ffffff",
      bgSurfaceHover: "#f8f9fa",
      textPrimary: "#1a1a1a",
      textSecondary: "#4a4a4a",
      textTertiary: "#6b6b6b",
      primary: "#667eea",
      primaryDark: "#5568d3",
      success: "#2ed573",
      warning: "#ffa502",
      error: "#ff4757",
      info: "#3498db",
      border: "rgba(0, 0, 0, 0.1)",
      borderLight: "rgba(0, 0, 0, 0.05)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#ffffff",
      glassBorderColor: "#000000",
      shadowColor: "#1f2687",
    },
  },
  dark: {
    id: "dark",
    category: "minimal",
    name: "Dark",
    description: "Vibrant dark mode",
    colors: {
      bgApp: "#0a0e1a",
      bgSurface: "#151b2e",
      bgSurfaceHover: "#1f2937",
      textPrimary: "#f0f4f8",
      textSecondary: "#c4cdd5",
      textTertiary: "#8b95a5",
      primary: "#7c3aed",
      primaryDark: "#6d28d9",
      success: "#10b981",
      warning: "#f59e0b",
      error: "#ef4444",
      info: "#3b82f6",
      border: "rgba(255, 255, 255, 0.12)",
      borderLight: "rgba(255, 255, 255, 0.06)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
  ocean: {
    id: "ocean",
    category: "vibrant",
    name: "Ocean",
    description: "Deep blue waters",
    colors: {
      bgApp: "#0a1929",
      bgSurface: "#132f4c",
      bgSurfaceHover: "#1e4976",
      textPrimary: "#e3f2fd",
      textSecondary: "#b3d9ff",
      textTertiary: "#7aa8d1",
      primary: "#00b4d8",
      primaryDark: "#0096c7",
      success: "#06ffa5",
      warning: "#ffb703",
      error: "#ff006e",
      info: "#48cae4",
      border: "rgba(227, 242, 253, 0.12)",
      borderLight: "rgba(227, 242, 253, 0.06)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
  sunset: {
    id: "sunset",
    category: "vibrant",
    name: "Sunset",
    description: "Warm evening glow",
    colors: {
      bgApp: "#1a0f2e",
      bgSurface: "#2d1b4e",
      bgSurfaceHover: "#3d2663",
      textPrimary: "#fef3e2",
      textSecondary: "#f4d9c6",
      textTertiary: "#d4a574",
      primary: "#ff6b35",
      primaryDark: "#e85d31",
      success: "#06ffa5",
      warning: "#ffd23f",
      error: "#ff006e",
      info: "#a78bfa",
      border: "rgba(254, 243, 226, 0.12)",
      borderLight: "rgba(254, 243, 226, 0.06)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
  forest: {
    id: "forest",
    category: "vibrant",
    name: "Forest",
    description: "Natural earth tones",
    colors: {
      bgApp: "#0f1a0f",
      bgSurface: "#1a2e1a",
      bgSurfaceHover: "#243d24",
      textPrimary: "#e8f5e8",
      textSecondary: "#c1e1c1",
      textTertiary: "#8fbc8f",
      primary: "#52b788",
      primaryDark: "#40916c",
      success: "#95d5b2",
      warning: "#ffb703",
      error: "#d62828",
      info: "#4cc9f0",
      border: "rgba(232, 245, 232, 0.12)",
      borderLight: "rgba(232, 245, 232, 0.06)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
  lavender: {
    id: "lavender",
    category: "vibrant",
    name: "Lavender",
    description: "Soft purple dream",
    colors: {
      bgApp: "#faf5ff",
      bgSurface: "#f3e8ff",
      bgSurfaceHover: "#e9d5ff",
      textPrimary: "#2d0a4e",
      textSecondary: "#4a1772",
      textTertiary: "#6b21a8",
      primary: "#a855f7",
      primaryDark: "#9333ea",
      success: "#22c55e",
      warning: "#f59e0b",
      error: "#ef4444",
      info: "#3b82f6",
      border: "rgba(59, 7, 100, 0.12)",
      borderLight: "rgba(59, 7, 100, 0.06)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#ffffff",
      glassBorderColor: "#3b0764",
      shadowColor: "#000000",
    },
  },
  coral: {
    id: "coral",
    category: "vibrant",
    name: "Coral",
    description: "Warm coral reef",
    colors: {
      bgApp: "#fff5f5",
      bgSurface: "#ffe4e6",
      bgSurfaceHover: "#fecdd3",
      textPrimary: "#5c1515",
      textSecondary: "#7f1d1d",
      textTertiary: "#991b1b",
      primary: "#fb7185",
      primaryDark: "#f43f5e",
      success: "#10b981",
      warning: "#f59e0b",
      error: "#dc2626",
      info: "#06b6d4",
      border: "rgba(127, 29, 29, 0.12)",
      borderLight: "rgba(127, 29, 29, 0.06)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#ffffff",
      glassBorderColor: "#7f1d1d",
      shadowColor: "#000000",
    },
  },
  nord: {
    id: "nord",
    category: "minimal",
    name: "Nord",
    description: "Arctic, north-bluish",
    colors: {
      bgApp: "#2e3440",
      bgSurface: "#3b4252",
      bgSurfaceHover: "#434c5e",
      textPrimary: "#eceff4",
      textSecondary: "#d8dee9",
      textTertiary: "#a3be8c",
      primary: "#88c0d0",
      primaryDark: "#5e81ac",
      success: "#a3be8c",
      warning: "#ebcb8b",
      error: "#bf616a",
      info: "#81a1c1",
      border: "rgba(216, 222, 233, 0.1)",
      borderLight: "rgba(216, 222, 233, 0.05)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
  dracula: {
    id: "dracula",
    category: "minimal",
    name: "Dracula",
    description: "Dark with vibrant colors",
    colors: {
      bgApp: "#282a36",
      bgSurface: "#44475a",
      bgSurfaceHover: "#6272a4",
      textPrimary: "#f8f8f2",
      textSecondary: "#e6e6e6",
      textTertiary: "#bd93f9",
      primary: "#bd93f9",
      primaryDark: "#9580d4",
      success: "#50fa7b",
      warning: "#f1fa8c",
      error: "#ff5555",
      info: "#8be9fd",
      border: "rgba(248, 248, 242, 0.1)",
      borderLight: "rgba(248, 248, 242, 0.05)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
  monokai: {
    id: "monokai",
    category: "minimal",
    name: "Monokai",
    description: "Classic code editor",
    colors: {
      bgApp: "#272822",
      bgSurface: "#3e3d32",
      bgSurfaceHover: "#49483e",
      textPrimary: "#f8f8f2",
      textSecondary: "#cfcfc2",
      textTertiary: "#75715e",
      primary: "#66d9ef",
      primaryDark: "#4db8d8",
      success: "#a6e22e",
      warning: "#e6db74",
      error: "#f92672",
      info: "#66d9ef",
      border: "rgba(248, 248, 242, 0.1)",
      borderLight: "rgba(248, 248, 242, 0.05)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
  solarized: {
    id: "solarized",
    category: "minimal",
    name: "Solarized",
    description: "Precision colors",
    colors: {
      bgApp: "#002b36",
      bgSurface: "#073642",
      bgSurfaceHover: "#0f4552",
      textPrimary: "#fdf6e3",
      textSecondary: "#eee8d5",
      textTertiary: "#93a1a1",
      primary: "#268bd2",
      primaryDark: "#1e6fa8",
      success: "#859900",
      warning: "#b58900",
      error: "#dc322f",
      info: "#2aa198",
      border: "rgba(253, 246, 227, 0.1)",
      borderLight: "rgba(253, 246, 227, 0.05)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
  gruvbox: {
    id: "gruvbox",
    category: "minimal",
    name: "Gruvbox",
    description: "Retro groove",
    colors: {
      bgApp: "#282828",
      bgSurface: "#3c3836",
      bgSurfaceHover: "#504945",
      textPrimary: "#ebdbb2",
      textSecondary: "#d5c4a1",
      textTertiary: "#a89984",
      primary: "#83a598",
      primaryDark: "#689d6a",
      success: "#b8bb26",
      warning: "#fabd2f",
      error: "#fb4934",
      info: "#83a598",
      border: "rgba(235, 219, 178, 0.1)",
      borderLight: "rgba(235, 219, 178, 0.05)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
  tokyoNight: {
    id: "tokyoNight",
    category: "futuristic",
    name: "Tokyo Night",
    description: "Clean dark theme",
    colors: {
      bgApp: "#1a1b26",
      bgSurface: "#24283b",
      bgSurfaceHover: "#2f3549",
      textPrimary: "#c0caf5",
      textSecondary: "#a9b1d6",
      textTertiary: "#565f89",
      primary: "#7aa2f7",
      primaryDark: "#5a7ec7",
      success: "#9ece6a",
      warning: "#e0af68",
      error: "#f7768e",
      info: "#7dcfff",
      border: "rgba(192, 202, 245, 0.1)",
      borderLight: "rgba(192, 202, 245, 0.05)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
  catppuccin: {
    id: "catppuccin",
    category: "minimal",
    name: "Catppuccin",
    description: "Soothing pastel",
    colors: {
      bgApp: "#1e1e2e",
      bgSurface: "#313244",
      bgSurfaceHover: "#45475a",
      textPrimary: "#cdd6f4",
      textSecondary: "#bac2de",
      textTertiary: "#a6adc8",
      primary: "#89b4fa",
      primaryDark: "#6a8ec7",
      success: "#a6e3a1",
      warning: "#f9e2af",
      error: "#f38ba8",
      info: "#89dceb",
      border: "rgba(205, 214, 244, 0.1)",
      borderLight: "rgba(205, 214, 244, 0.05)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
  oneDark: {
    id: "oneDark",
    category: "minimal",
    name: "One Dark",
    description: "Atom's iconic theme",
    colors: {
      bgApp: "#282c34",
      bgSurface: "#2c313a",
      bgSurfaceHover: "#3e4451",
      textPrimary: "#abb2bf",
      textSecondary: "#9da5b4",
      textTertiary: "#5c6370",
      primary: "#61afef",
      primaryDark: "#4a8ec7",
      success: "#98c379",
      warning: "#e5c07b",
      error: "#e06c75",
      info: "#56b6c2",
      border: "rgba(171, 178, 191, 0.1)",
      borderLight: "rgba(171, 178, 191, 0.05)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
  material: {
    id: "material",
    category: "minimal",
    name: "Material",
    description: "Google Material Design",
    colors: {
      bgApp: "#263238",
      bgSurface: "#37474f",
      bgSurfaceHover: "#455a64",
      textPrimary: "#eceff1",
      textSecondary: "#cfd8dc",
      textTertiary: "#90a4ae",
      primary: "#80cbc4",
      primaryDark: "#5fa39a",
      success: "#c3e88d",
      warning: "#ffcb6b",
      error: "#f07178",
      info: "#89ddff",
      border: "rgba(236, 239, 241, 0.1)",
      borderLight: "rgba(236, 239, 241, 0.05)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
  synthwave: {
    id: "synthwave",
    category: "futuristic",
    name: "Synthwave",
    description: "Outrun cyberpunk",
    colors: {
      bgApp: "#241b2f",
      bgSurface: "#2a2139",
      bgSurfaceHover: "#34294f",
      textPrimary: "#f8f8f2",
      textSecondary: "#e0d9f0",
      textTertiary: "#b4a5d8",
      primary: "#ff7edb",
      primaryDark: "#d65fb8",
      success: "#72f1b8",
      warning: "#fede5d",
      error: "#fe4450",
      info: "#36f9f6",
      border: "rgba(248, 248, 242, 0.1)",
      borderLight: "rgba(248, 248, 242, 0.05)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
  rosePine: {
    id: "rosePine",
    category: "minimal",
    name: "Rosé Pine",
    description: "Natural pine vibes",
    colors: {
      bgApp: "#191724",
      bgSurface: "#1f1d2e",
      bgSurfaceHover: "#26233a",
      textPrimary: "#e0def4",
      textSecondary: "#908caa",
      textTertiary: "#6e6a86",
      primary: "#c4a7e7",
      primaryDark: "#9c7ec0",
      success: "#9ccfd8",
      warning: "#f6c177",
      error: "#eb6f92",
      info: "#31748f",
      border: "rgba(224, 222, 244, 0.1)",
      borderLight: "rgba(224, 222, 244, 0.05)",
      scrollbarThumb: "rgba(107, 115, 255, 0.4)",
      scrollbarThumbHover: "rgba(107, 115, 255, 0.6)",
      scrollbarThumbActive: "rgba(107, 115, 255, 0.8)",
      glassColor: "#1e2128",
      glassBorderColor: "#ffffff",
      shadowColor: "#000000",
    },
  },
};

// --- Fonts ---
export type FontCategory =
  | "professional"
  | "clean"
  | "fun"
  | "cool"
  | "quirky"
  | "minimal";

export interface FontTheme {
  id: string;
  name: string;
  fontFamily: string;
  category: FontCategory;
}

export const fontThemes: Record<string, FontTheme> = {
  // Professional Fonts
  inter: {
    id: "inter",
    name: "Inter",
    fontFamily: '"Inter", sans-serif',
    category: "professional",
  },
  roboto: {
    id: "roboto",
    name: "Roboto",
    fontFamily: '"Roboto", sans-serif',
    category: "professional",
  },
  poppins: {
    id: "poppins",
    name: "Poppins",
    fontFamily: '"Poppins", sans-serif',
    category: "professional",
  },
  montserrat: {
    id: "montserrat",
    name: "Montserrat",
    fontFamily: '"Montserrat", sans-serif',
    category: "professional",
  },
  playfair: {
    id: "playfair",
    name: "Playfair Display",
    fontFamily: '"Playfair Display", serif',
    category: "professional",
  },

  // Clean Fonts
  lato: {
    id: "lato",
    name: "Lato",
    fontFamily: '"Lato", sans-serif',
    category: "clean",
  },
  openSans: {
    id: "openSans",
    name: "Open Sans",
    fontFamily: '"Open Sans", sans-serif',
    category: "clean",
  },
  raleway: {
    id: "raleway",
    name: "Raleway",
    fontFamily: '"Raleway", sans-serif',
    category: "clean",
  },
  nunito: {
    id: "nunito",
    name: "Nunito",
    fontFamily: '"Nunito", sans-serif',
    category: "clean",
  },

  // Fun Fonts
  quicksand: {
    id: "quicksand",
    name: "Quicksand",
    fontFamily: '"Quicksand", sans-serif',
    category: "fun",
  },
  pacifico: {
    id: "pacifico",
    name: "Pacifico",
    fontFamily: '"Pacifico", cursive',
    category: "fun",
  },
  lobster: {
    id: "lobster",
    name: "Lobster",
    fontFamily: '"Lobster", cursive',
    category: "fun",
  },
  comfortaa: {
    id: "comfortaa",
    name: "Comfortaa",
    fontFamily: '"Comfortaa", cursive',
    category: "fun",
  },
  fredoka: {
    id: "fredoka",
    name: "Fredoka",
    fontFamily: '"Fredoka", sans-serif',
    category: "fun",
  },

  // Cool Fonts
  righteous: {
    id: "righteous",
    name: "Righteous",
    fontFamily: '"Righteous", cursive',
    category: "cool",
  },
  bebasNeue: {
    id: "bebasNeue",
    name: "Bebas Neue",
    fontFamily: '"Bebas Neue", cursive',
    category: "cool",
  },
  oswald: {
    id: "oswald",
    name: "Oswald",
    fontFamily: '"Oswald", sans-serif',
    category: "cool",
  },
  orbitron: {
    id: "orbitron",
    name: "Orbitron",
    fontFamily: '"Orbitron", sans-serif',
    category: "cool",
  },

  // Quirky Fonts
  spaceGrotesk: {
    id: "spaceGrotesk",
    name: "Space Grotesk",
    fontFamily: '"Space Grotesk", sans-serif',
    category: "quirky",
  },
  caveat: {
    id: "caveat",
    name: "Caveat",
    fontFamily: '"Caveat", cursive',
    category: "quirky",
  },
  satisfy: {
    id: "satisfy",
    name: "Satisfy",
    fontFamily: '"Satisfy", cursive',
    category: "quirky",
  },
  dancingScript: {
    id: "dancingScript",
    name: "Dancing Script",
    fontFamily: '"Dancing Script", cursive',
    category: "quirky",
  },

  // Minimal Fonts
  firaCode: {
    id: "firaCode",
    name: "Fira Code",
    fontFamily: '"Fira Code", monospace',
    category: "minimal",
  },
  courierPrime: {
    id: "courierPrime",
    name: "Courier Prime",
    fontFamily: '"Courier Prime", monospace',
    category: "minimal",
  },
  ibmPlexMono: {
    id: "ibmPlexMono",
    name: "IBM Plex Mono",
    fontFamily: '"IBM Plex Mono", monospace',
    category: "minimal",
  },
  jetBrainsMono: {
    id: "jetBrainsMono",
    name: "JetBrains Mono",
    fontFamily: '"JetBrains Mono", monospace',
    category: "minimal",
  },
};

// --- Effects ---
export interface EffectSettings {
  glowStrength: number; // 0 to 100
  glassOpacity: number; // 0 to 100
  glassBlur: number; // 0 to 20 (px)
  shadowStrength: number; // 0 to 100
  borderRadius: number; // 0 to 24 (px)
  fabRoundness: number; // 0 to 100 (0 = square, 100 = round)
  parallaxStrength: number; // 0 to 100
  pulsingStrength: number; // 0 to 100 (0 = no pulse, 100 = max pulse scale)
  animationSpeed: number; // 0.5 to 2.0 (multiplier)
}

export const defaultEffectSettings: EffectSettings = {
  glowStrength: 50,
  glassOpacity: 70,
  glassBlur: 10,
  shadowStrength: 40,
  borderRadius: 12,
  fabRoundness: 25, // Slightly rounded square by default
  parallaxStrength: 25, // Moderate parallax (0-100, converts to 0-10 degrees max tilt)
  pulsingStrength: 50, // Medium pulse intensity by default
  animationSpeed: 1.0,
};

// --- Utilities ---

// Helper to convert hex to rgb
const hexToRgb = (hex: string): string => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(
        result[3],
        16
      )}`
    : "0, 0, 0";
};

// Helper to calculate relative luminance of a color (0 = black, 1 = white)
const getLuminance = (hex: string): number => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return 0;

  const r = parseInt(result[1], 16) / 255;
  const g = parseInt(result[2], 16) / 255;
  const b = parseInt(result[3], 16) / 255;

  // Apply sRGB gamma correction
  const rsRGB = r <= 0.03928 ? r / 12.92 : Math.pow((r + 0.055) / 1.055, 2.4);
  const gsRGB = g <= 0.03928 ? g / 12.92 : Math.pow((g + 0.055) / 1.055, 2.4);
  const bsRGB = b <= 0.03928 ? b / 12.92 : Math.pow((b + 0.055) / 1.055, 2.4);

  return 0.2126 * rsRGB + 0.7152 * gsRGB + 0.0722 * bsRGB;
};

export const getThemeCssVariables = (
  colorTheme: ColorTheme,
  fontTheme: FontTheme,
  effects: EffectSettings
): React.CSSProperties => {
  const cssVars: Record<string, string | number> = {};

  // Apply Colors
  Object.entries(colorTheme.colors).forEach(([key, value]) => {
    // Convert camelCase to kebab-case for CSS variables
    const cssVar = `--${key.replace(/([A-Z])/g, "-$1").toLowerCase()}`;
    cssVars[cssVar] = value;
  });

  // Apply Fonts
  cssVars["--font-default"] = fontTheme.fontFamily;

  // Apply Effects
  cssVars["--glow-strength"] = effects.glowStrength.toString();
  cssVars["--glass-opacity"] = (effects.glassOpacity / 100).toString();
  cssVars["--glass-blur"] = `${effects.glassBlur}px`;
  cssVars["--shadow-strength"] = effects.shadowStrength.toString(); // Pass raw 0-100 for CSS calc
  cssVars["--border-radius"] = `${effects.borderRadius}px`;
  cssVars["--parallax-strength"] = (effects.parallaxStrength || 0).toString();
  cssVars["--pulsing-strength"] = (effects.pulsingStrength ?? 50).toString();
  cssVars["--animation-speed"] = (effects.animationSpeed || 1).toString();

  // Animation Durations
  const speed = effects.animationSpeed || 1;
  cssVars["--duration-fast"] = `${0.15 / speed}s`;
  cssVars["--duration-normal"] = `${0.3 / speed}s`;
  cssVars["--duration-slow"] = `${0.5 / speed}s`;

  // Dynamic Glass Effects
  const glassRgb = hexToRgb(colorTheme.colors.glassColor);
  const glassBorderRgb = hexToRgb(colorTheme.colors.glassBorderColor);

  cssVars["--glass-bg"] = `rgba(${glassRgb}, ${effects.glassOpacity / 100})`;
  const borderOpacity = 0.05 + effects.glassOpacity / 200;
  cssVars["--glass-border"] = `rgba(${glassBorderRgb}, ${borderOpacity})`;

  // Dynamic Shadow
  const shadowRgb = hexToRgb(colorTheme.colors.shadowColor);
  const shadowOpacity = effects.shadowStrength / 100;
  cssVars[
    "--glass-shadow"
  ] = `0 8px 32px 0 rgba(${shadowRgb}, ${shadowOpacity})`;
  cssVars["--shadow"] = `rgba(${shadowRgb}, ${shadowOpacity})`;

  // Dynamic Glows - Adjusted for theme brightness
  // Detect if theme is light or dark based on background luminance
  const bgLuminance = getLuminance(colorTheme.colors.bgApp);
  const isLightTheme = bgLuminance > 0.5;

  // For light themes, increase glow opacity to make it more visible
  // For dark themes, decrease glow opacity to prevent overpowering effect
  const baseGlowOpacity = isLightTheme ? 0.15 : 0.08;
  const maxGlowBoost = isLightTheme ? 0.35 : 0.25;
  const glowOpacity =
    baseGlowOpacity + (effects.glowStrength / 100) * maxGlowBoost;

  const primaryRgb = hexToRgb(colorTheme.colors.primary);
  const successRgb = hexToRgb(colorTheme.colors.success);
  const warningRgb = hexToRgb(colorTheme.colors.warning);
  const errorRgb = hexToRgb(colorTheme.colors.error);

  cssVars["--primary-rgb"] = primaryRgb;
  cssVars["--glow-primary"] = `rgba(${primaryRgb}, ${glowOpacity})`;
  cssVars["--glow-success"] = `rgba(${successRgb}, ${glowOpacity})`;
  cssVars["--glow-warning"] = `rgba(${warningRgb}, ${glowOpacity})`;
  cssVars["--glow-danger"] = `rgba(${errorRgb}, ${glowOpacity})`;

  // Calculate FAB border radius based on percentage
  const fabRadius = 4 + (effects.fabRoundness / 100) * 24; // Max 28px (half of 56px FAB)
  cssVars["--fab-radius"] =
    effects.fabRoundness === 100 ? "50%" : `${fabRadius}px`;

  return cssVars;
};

export const applyTheme = (
  colorTheme: ColorTheme,
  fontTheme: FontTheme,
  effects: EffectSettings
) => {
  const root = document.documentElement;
  const cssVars = getThemeCssVariables(colorTheme, fontTheme, effects);

  Object.entries(cssVars).forEach(([key, value]) => {
    root.style.setProperty(key, value as string);
  });
};

export const loadSavedTheme = () => {
  try {
    const saved = localStorage.getItem("theme_preference");
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (e) {
    console.error("Failed to load theme", e);
  }
  return null;
};

export const saveTheme = (
  colorId: string,
  fontId: string,
  effects: EffectSettings
) => {
  try {
    localStorage.setItem(
      "theme_preference",
      JSON.stringify({
        colorId,
        fontId,
        effects,
      })
    );
  } catch (e) {
    console.error("Failed to save theme", e);
  }
};

export const getTheme = (id: string): ColorTheme => {
  return colorThemes[id] || colorThemes.light;
};
