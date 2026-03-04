/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Sora', 'sans-serif'],
        body: ['DM Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        koisk: {
          navy:    '#0F2044',
          blue:    '#1A3A6B',
          teal:    '#0B6E6E',
          accent:  '#00C9A7',
          amber:   '#F59E0B',
          danger:  '#EF4444',
          success: '#10B981',
          surface: '#F0F4FA',
          muted:   '#8896B3',
        },
      },
      animation: {
        'fade-up':    'fadeUp 0.4s ease forwards',
        'fade-in':    'fadeIn 0.3s ease forwards',
        'pulse-ring': 'pulseRing 1.2s ease-out infinite',
        'slide-in':   'slideIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'bounce-in':  'bounceIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards',
      },
      keyframes: {
        fadeUp: {
          from: { opacity: 0, transform: 'translateY(16px)' },
          to:   { opacity: 1, transform: 'translateY(0)' },
        },
        fadeIn: {
          from: { opacity: 0 },
          to:   { opacity: 1 },
        },
        pulseRing: {
          '0%':   { transform: 'scale(0.8)', opacity: 1 },
          '100%': { transform: 'scale(2)',   opacity: 0 },
        },
        slideIn: {
          from: { opacity: 0, transform: 'translateX(-24px)' },
          to:   { opacity: 1, transform: 'translateX(0)' },
        },
        bounceIn: {
          from: { opacity: 0, transform: 'scale(0.6)' },
          to:   { opacity: 1, transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [],
}
