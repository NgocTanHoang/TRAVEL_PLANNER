/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
    "./apps/**/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#153D68',
        'primary-light': '#1e4d7f',
        'primary-dark': '#0d2842',
        secondary: '#00838F',
        'secondary-light': '#00a5b5',
        'secondary-dark': '#00616b',
        accent: '#DAA520',
        'accent-light': '#f0c040',
        'accent-dark': '#b8860b',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        heading: ['Poppins', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
