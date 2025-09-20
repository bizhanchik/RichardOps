/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        // Dark theme colors
        dark: {
          bg: '#0a0a0a',
          surface: '#111111',
          card: '#1a1a1a',
          border: '#262626',
        },
        // Neon purple accents
        neon: {
          purple: {
            100: '#f3e8ff',
            200: '#e9d5ff',
            300: '#d8b4fe',
            400: '#c084fc',
            500: '#a855f7',
            600: '#9333ea',
            700: '#7c3aed',
            800: '#6b21a8',
            900: '#581c87',
          },
          // Neon green accents
          green: {
            100: '#dcfce7',
            200: '#bbf7d0',
            300: '#86efac',
            400: '#4ade80',
            500: '#22c55e',
            600: '#16a34a',
            700: '#15803d',
            800: '#166534',
            900: '#14532d',
          },
        },
        // Text colors for dark theme
        text: {
          primary: '#ffffff',
          secondary: '#e5e5e5',
          muted: '#a3a3a3',
          accent: '#a855f7',
        }
      },
      backgroundImage: {
        'gradient-dark': 'linear-gradient(135deg, #0a0a0a 0%, #111111 100%)',
        'gradient-neon': 'linear-gradient(135deg, #a855f7 0%, #22c55e 100%)',
        'gradient-purple': 'linear-gradient(135deg, #7c3aed 0%, #a855f7 100%)',
        'gradient-green': 'linear-gradient(135deg, #15803d 0%, #22c55e 100%)',
      },
      boxShadow: {
        'neon-purple': '0 0 20px rgba(168, 85, 247, 0.3)',
        'neon-green': '0 0 20px rgba(34, 197, 94, 0.3)',
        'card-dark': '0 4px 12px rgba(0, 0, 0, 0.4)',
        'card-hover': '0 8px 32px rgba(168, 85, 247, 0.2)',
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite alternate',
        'float': 'float 3s ease-in-out infinite',
        'slide-up': 'slideUp 0.5s ease-out',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(168, 85, 247, 0.3)' },
          '100%': { boxShadow: '0 0 30px rgba(168, 85, 247, 0.6)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0px)' },
        },
      },
    },
  },
  plugins: [],
}