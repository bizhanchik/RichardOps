/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme colors - only used ones
        dark: {
          bg: '#0a0a0a',
          surface: '#111111',
          card: '#1a1a1a',
        },
        // Neon colors - only used variants
        neon: {
          purple: {
            500: '#a855f7',
            900: '#581c87',
          },
          green: {
            500: '#22c55e',
            900: '#14532d',
          },
        },
        // Text colors for dark theme
        text: {
          primary: '#ffffff',
          secondary: '#e5e5e5',
          muted: '#a3a3a3',
        }
      },
      backgroundImage: {
        'gradient-neon': 'linear-gradient(135deg, #a855f7 0%, #22c55e 100%)',
        'gradient-purple': 'linear-gradient(135deg, #7c3aed 0%, #a855f7 100%)',
        'gradient-green': 'linear-gradient(135deg, #15803d 0%, #22c55e 100%)',
      },
    },
  },
  plugins: [],
}