/** Design tokens from docs/design.md (dark theme). */
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        bg: '#0E0E12',
        surface: '#1A1A22',
        'surface-2': '#24242E',
        border: '#2E2E3A',
        text: '#F5F5F7',
        'text-muted': '#A0A0AE',
        primary: '#B6FF3B',
        'on-primary': '#0E0E12',
        accent: '#FF3BD4',
        'speaker-a': '#3BC8FF',
        'speaker-b': '#FFB23B',
        danger: '#FF4D4D',
        success: '#3BFF8A',
      },
      fontSize: {
        display: ['32px', { lineHeight: '38px', fontWeight: '800' }],
        title: ['22px', { lineHeight: '28px', fontWeight: '700' }],
        body: ['16px', { lineHeight: '24px' }],
        label: ['14px', { lineHeight: '20px', fontWeight: '600' }],
        caption: ['12px', { lineHeight: '16px', fontWeight: '500' }],
      },
      borderRadius: {
        sm: '8px',
        md: '12px',
        lg: '20px',
      },
    },
  },
  plugins: [],
};
