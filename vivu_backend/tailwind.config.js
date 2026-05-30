/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
    './static/**/*.js',
    './apps/**/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--background-hex)',
        foreground: 'var(--foreground-hex)',
        muted: {
          DEFAULT: 'var(--muted-hex)',
          foreground: 'var(--muted-foreground-hex)',
        },
        card: {
          DEFAULT: 'var(--card-hex)',
          foreground: 'var(--card-foreground-hex)',
        },
        border: 'var(--border-hex)',
        input: 'var(--input-hex)',
        primary: {
          DEFAULT: 'var(--primary-hex)',
          hover: 'var(--primary-hover-hex)',
          foreground: 'var(--primary-foreground-hex)',
        },
        secondary: {
          DEFAULT: 'var(--secondary-hex)',
          foreground: 'var(--secondary-foreground-hex)',
        },
        accent: {
          DEFAULT: 'var(--accent-hex)',
          hover: 'var(--accent-hover-hex)',
          foreground: 'var(--accent-foreground-hex)',
        },
        ocean: {
          DEFAULT: 'var(--ocean-hex)',
          soft: 'var(--ocean-soft-hex)',
        },
        emerald: {
          soft: 'var(--emerald-soft-hex)',
        },
        warning: {
          DEFAULT: 'var(--warning-hex)',
          soft: 'var(--warning-soft-hex)',
          foreground: 'var(--warning-foreground-hex)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        heading: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 18px 45px rgba(15, 23, 42, 0.10)',
      },
    },
  },
  plugins: [],
};
