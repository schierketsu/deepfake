/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: '#1F2126',
        paper: '#DCDDE1',
        soft: {
          50: '#F4F5F7',
          100: '#ECEEF2',
          200: '#D6D9E0',
          300: '#B8BEC9',
          400: '#979FAD',
          500: '#767F90',
          600: '#5A6170',
          700: '#424754',
          800: '#262626',
          900: '#1C1F27',
        },
        accent: {
          50: '#EFF7FF',
          100: '#DBECFF',
          200: '#BDD9FF',
          300: '#41A5F3',
          400: '#5BA8F5',
          500: '#2F93E6',
          600: '#2476C0',
          700: '#205C96',
          800: '#1E507D',
          900: '#1E4468',
        },
        success: '#38B68A',
        warning: '#E8B44C',
        danger: '#D56476',
      },
      fontFamily: {
        sans: ['"PF Centro Sans Pro"', 'Inter', 'system-ui', 'sans-serif'],
        display: ['"PF Centro Sans Pro"', 'Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'display-xl': ['3.25rem', { lineHeight: '1.06', letterSpacing: '-0.02em' }],
        'display-lg': ['2.5rem', { lineHeight: '1.08', letterSpacing: '-0.02em' }],
        'heading-xl': ['1.75rem', { lineHeight: '1.2', letterSpacing: '-0.01em' }],
        'heading-lg': ['1.375rem', { lineHeight: '1.25' }],
        'body-lg': ['1.0625rem', { lineHeight: '1.6' }],
      },
      borderRadius: {
        '2xl': '1.25rem',
        '3xl': '1.75rem',
      },
      boxShadow: {
        soft: '0 8px 24px rgba(36, 41, 56, 0.08)',
        'soft-lg': '0 16px 36px rgba(36, 41, 56, 0.12)',
      },
      maxWidth: {
        shell: '1120px',
      },
      spacing: {
        18: '4.5rem',
      },
    },
  },
  plugins: [],
}
