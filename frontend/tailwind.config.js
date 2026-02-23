/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: '#111827',
        paper: '#f9fafb',
        soft: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        },
        accent: {
          300: '#9ca3af',
          400: '#6b7280',
          500: '#4b5563',
        },
        success: '#059669',
        warning: '#d97706',
        danger: '#dc2626',
      },
      fontFamily: {
        sans: ['JetBrains Mono', 'Consolas', 'Monaco', 'monospace'],
        polonium: ['Polonium', 'sans-serif'],
      },
      fontWeight: {
        normal: '400',
        medium: '500',
      },
      maxWidth: {
        shell: '1100px',
      },
    },
  },
  plugins: [],
}
