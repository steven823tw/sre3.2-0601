/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#0f1117",
          secondary: "#1a1d24",
          tertiary: "#22252e",
          hover: "#2a2d36",
        },
        text: {
          primary: "#e0e0e0",
          secondary: "#757575",
        },
        accent: {
          DEFAULT: "#00BFA5",
          hover: "#00E5B0",
        },
        info: "#448AFF",
        warning: "#FFB300",
        danger: "#FF5252",
        success: "#69F0AE",
        border: "#2a2d36",
      },
      animation: {
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-in-right": "slideInRight 0.3s ease-out",
        "slide-up": "slideUp 0.2s ease-out",
        "loading-dot": "loadingDot 1.4s infinite ease-in-out both",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(-4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          "0%": { transform: "translateX(100%)" },
          "100%": { transform: "translateX(0)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        loadingDot: {
          "0%, 80%, 100%": { transform: "scale(0)" },
          "40%": { transform: "scale(1)" },
        },
      },
    },
  },
  plugins: [],
};
