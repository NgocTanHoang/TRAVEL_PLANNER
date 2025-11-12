/**
 * ============================================================================
 * VI VU - TAILWIND CSS CONFIGURATION
 * ============================================================================
 * 
 * Brand Color System: 60:30:10 Rule
 * - 60% Primary: Deep Navy Blue (#153D68)
 * - 30% Secondary: Deep Teal (#00838F)
 * - 10% Accent: Golden Amber (#DAA520)
 * 
 * Typography: Inter (body) + Poppins (headings)
 * ============================================================================
 */

module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
    "../**/*.html",
  ],
  
  darkMode: 'class', // or 'media' for automatic dark mode
  
  theme: {
    extend: {
      // ========================================
      // BRAND COLORS - 60:30:10 System
      // ========================================
      colors: {
        // 60% PRIMARY - Deep Navy Blue
        primary: {
          DEFAULT: '#153D68',
          light: '#1e4d7f',
          dark: '#0d2842',
          50: '#f0f4f8',
          100: '#d9e2ec',
          200: '#bcccdc',
          300: '#9fb3c8',
          400: '#829ab1',
          500: '#627d98',
          600: '#486581',
          700: '#334e68',
          800: '#243b53',
          900: '#153D68',
          950: '#0d2842',
        },
        
        // 30% SECONDARY - Deep Teal
        secondary: {
          DEFAULT: '#00838F',
          light: '#00a5b5',
          dark: '#00616b',
          50: '#e0f7fa',
          100: '#b2ebf2',
          200: '#80deea',
          300: '#4dd0e1',
          400: '#26c6da',
          500: '#00bcd4',
          600: '#00acc1',
          700: '#0097a7',
          800: '#00838F',
          900: '#00616b',
          950: '#004d56',
        },
        
        // 10% ACCENT - Golden Amber
        accent: {
          DEFAULT: '#DAA520',
          light: '#f0c040',
          dark: '#b8860b',
          50: '#fefcf0',
          100: '#fef8d9',
          200: '#fdefb3',
          300: '#fce58c',
          400: '#fadb66',
          500: '#f9d240',
          600: '#f3c423',
          700: '#DAA520',
          800: '#b8860b',
          900: '#9a7109',
          950: '#6b4f06',
        },
        
        // SEMANTIC COLORS
        success: {
          DEFAULT: '#10B981',
          light: '#34D399',
          dark: '#059669',
        },
        warning: {
          DEFAULT: '#F59E0B',
          light: '#FBBF24',
          dark: '#D97706',
        },
        error: {
          DEFAULT: '#EF4444',
          light: '#F87171',
          dark: '#DC2626',
        },
      },
      
      // ========================================
      // TYPOGRAPHY
      // ========================================
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        heading: ['Poppins', 'Inter', 'sans-serif'],
        mono: ['Fira Code', 'Courier New', 'monospace'],
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
        '7xl': ['4.5rem', { lineHeight: '1' }],
        '8xl': ['6rem', { lineHeight: '1' }],
        '9xl': ['8rem', { lineHeight: '1' }],
      },
      
      fontWeight: {
        light: '300',
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
        extrabold: '800',
        black: '900',
      },
      
      letterSpacing: {
        tighter: '-0.05em',
        tight: '-0.025em',
        normal: '0em',
        wide: '0.025em',
        wider: '0.05em',
        widest: '0.1em',
      },
      
      // ========================================
      // SPACING
      // ========================================
      spacing: {
        '128': '32rem',
        '144': '36rem',
      },
      
      // ========================================
      // BORDER RADIUS
      // ========================================
      borderRadius: {
        'none': '0',
        'sm': '0.375rem',
        DEFAULT: '0.5rem',
        'md': '0.5rem',
        'lg': '0.75rem',
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
        'full': '9999px',
      },
      
      // ========================================
      // BOX SHADOWS
      // ========================================
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        DEFAULT: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        'inner': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
        'none': 'none',
        
        // Brand-colored shadows
        'primary': '0 10px 25px -5px rgba(21, 61, 104, 0.3)',
        'secondary': '0 10px 25px -5px rgba(0, 131, 143, 0.3)',
        'accent': '0 10px 25px -5px rgba(218, 165, 32, 0.3)',
      },
      
      // ========================================
      // TRANSITIONS
      // ========================================
      transitionDuration: {
        'fast': '150ms',
        DEFAULT: '300ms',
        'slow': '500ms',
      },
      
      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      
      // ========================================
      // Z-INDEX
      // ========================================
      zIndex: {
        'dropdown': '1000',
        'sticky': '1020',
        'fixed': '1030',
        'modal-backdrop': '1040',
        'modal': '1050',
        'popover': '1060',
        'tooltip': '1070',
      },
      
      // ========================================
      // ANIMATIONS
      // ========================================
      keyframes: {
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(100%)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'slide-down': {
          '0%': { transform: 'translateY(-100%)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'fade-in': 'fade-in 0.3s ease-in',
        'slide-up': 'slide-up 0.3s ease-out',
        'slide-down': 'slide-down 0.3s ease-out',
      },
    },
  },
  
  plugins: [
    // Optional: Add Tailwind plugins here
    // require('@tailwindcss/forms'),
    // require('@tailwindcss/typography'),
    // require('@tailwindcss/aspect-ratio'),
  ],
}

