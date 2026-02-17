import type { Config } from 'tailwindcss'

/**
 * Tailwind CSS Configuration
 * 
 * This configuration extends Tailwind with custom design tokens that map to CSS variables
 * defined in tokens.css. This enables real-time customization through the Customization Engine
 * without requiring Tailwind rebuilds.
 * 
 * Requirements: 1.1, 1.3, 1.4, 1.5, 1.6
 */
const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      // Color tokens (Requirement 1.3)
      // Using CSS variables for real-time customization
      colors: {
        // Primary colors
        primary: {
          DEFAULT: 'var(--primary)',
          dark: 'var(--primary-dark)',
        },
        
        // Background colors
        bg: {
          app: 'var(--bg-app)',
          surface: 'var(--bg-surface)',
          'surface-hover': 'var(--bg-surface-hover)',
          glass: 'var(--glass-bg)',
        },
        
        // Text colors
        text: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          tertiary: 'var(--text-tertiary)',
          muted: 'var(--text-tertiary)',
        },
        
        // Status colors
        status: {
          success: 'var(--success)',
          'success-bg': 'var(--status-success-bg)',
          'success-text': 'var(--status-success-text)',
          warning: 'var(--warning)',
          'warning-bg': 'var(--status-warning-bg)',
          'warning-text': 'var(--status-warning-text)',
          error: 'var(--error)',
          'error-bg': 'var(--status-error-bg)',
          'error-text': 'var(--status-error-text)',
          info: 'var(--info)',
          'info-bg': 'var(--status-info-bg)',
          'info-text': 'var(--status-info-text)',
        },
        
        // Border colors
        border: {
          DEFAULT: 'var(--border)',
          light: 'var(--border-light)',
          glass: 'var(--glass-border)',
        },
        
        // Glow colors
        glow: {
          primary: 'var(--glow-primary)',
          success: 'var(--glow-success)',
          warning: 'var(--glow-warning)',
          danger: 'var(--glow-danger)',
        },
      },
      
      // Spacing tokens (Requirement 1.5)
      // Using 4px base unit: space-n = n * 4px
      spacing: {
        'space-1': 'var(--space-1, 4px)',
        'space-2': 'var(--space-2, 8px)',
        'space-3': 'var(--space-3, 12px)',
        'space-4': 'var(--space-4, 16px)',
        'space-5': 'var(--space-5, 20px)',
        'space-6': 'var(--space-6, 24px)',
        'space-7': 'var(--space-7, 28px)',
        'space-8': 'var(--space-8, 32px)',
      },
      
      // Typography tokens (Requirement 1.6)
      fontFamily: {
        default: 'var(--font-default)',
        corporate: 'var(--font-corporate)',
        fun: 'var(--font-fun)',
        nerd: 'var(--font-nerd)',
        quirky: 'var(--font-quirky)',
      },
      
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
        '6xl': ['3.75rem', { lineHeight: '1' }],
      },
      
      // Effect tokens (Requirement 1.4)
      backdropBlur: {
        glass: 'var(--glass-blur, 10px)',
      },
      
      borderRadius: {
        DEFAULT: 'var(--border-radius, 12px)',
        glass: 'var(--border-radius, 12px)',
        fab: 'var(--fab-radius, 14px)',
      },
      
      boxShadow: {
        glass: 'var(--glass-shadow)',
        sm: '0 2px 4px var(--shadow)',
        md: '0 4px 12px var(--shadow)',
        lg: '0 8px 24px var(--shadow)',
        glow: '0 0 20px var(--glow-primary)',
        'glow-success': '0 0 20px var(--glow-success)',
        'glow-warning': '0 0 20px var(--glow-warning)',
        'glow-danger': '0 0 20px var(--glow-danger)',
      },
      
      // Animation tokens (Requirement 1.4)
      transitionDuration: {
        fast: 'var(--duration-fast, 0.15s)',
        normal: 'var(--duration-normal, 0.3s)',
        slow: 'var(--duration-slow, 0.5s)',
      },
      
      // Keyframe animations
      keyframes: {
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
      },
      
      animation: {
        shimmer: 'shimmer 1.5s infinite',
      },
      
      // Opacity for glass effects
      opacity: {
        glass: 'var(--glass-opacity, 0.7)',
      },
      
      // Background opacity for glass panels
      backgroundOpacity: {
        glass: 'var(--glass-opacity, 0.7)',
      },
    },
  },
  plugins: [
    // Custom plugin for hiding scrollbars while maintaining scroll functionality
    function({ addUtilities }: { addUtilities: (utilities: Record<string, Record<string, string>>) => void }) {
      addUtilities({
        '.scrollbar-hide': {
          /* Hide scrollbar for IE, Edge and Firefox */
          '-ms-overflow-style': 'none',
          'scrollbar-width': 'none',
          /* Hide scrollbar for Chrome, Safari and Opera */
          '&::-webkit-scrollbar': {
            display: 'none',
          },
        },
      })
    },
  ],
}

export default config
